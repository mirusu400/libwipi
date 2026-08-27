use std::{
    env, fs,
    sync::{
        Arc, Mutex,
        atomic::{AtomicU32, AtomicUsize, Ordering},
    },
};

use test_utils::TestPlatform;
use wie_backend::{
    AudioSink, DatabaseRepository, Emulator, Event, Filesystem, Instant, KeyCode,
    Options, Platform, Screen, canvas::Image, extract_zip,
};
use wie_lgt::LgtEmulator;
use wie_util::Result;

#[derive(Default)]
struct ScreenStats {
    paints: AtomicUsize,
    width: AtomicU32,
    height: AtomicU32,
    nonzero_bytes: AtomicUsize,
    hashes: Mutex<Vec<u64>>,
}

struct RecordingScreen(Arc<ScreenStats>);

impl Screen for RecordingScreen {
    fn resize(&self, width: u32, height: u32) -> Result<()> {
        self.0.width.store(width, Ordering::SeqCst);
        self.0.height.store(height, Ordering::SeqCst);
        Ok(())
    }

    fn request_redraw(&self) -> Result<()> {
        Ok(())
    }

    fn paint(&self, image: &dyn Image) {
        let raw = image.raw();
        let mut hash = 0xcbf29ce484222325u64;
        let mut nonzero = 0usize;
        for byte in raw.iter().copied() {
            hash ^= u64::from(byte);
            hash = hash.wrapping_mul(0x100000001b3);
            nonzero += usize::from(byte != 0);
        }
        self.0.width.store(image.width(), Ordering::SeqCst);
        self.0.height.store(image.height(), Ordering::SeqCst);
        self.0.nonzero_bytes.store(nonzero, Ordering::SeqCst);
        self.0.hashes.lock().unwrap().push(hash);
        let paint = self.0.paints.fetch_add(1, Ordering::SeqCst) + 1;
        if paint <= 4 {
            println!("libwipi-platformer-frame paint={paint} hash={hash:016x}");
        }
    }

    fn width(&self) -> u32 {
        self.0.width.load(Ordering::SeqCst)
    }

    fn height(&self) -> u32 {
        self.0.height.load(Ordering::SeqCst)
    }
}

struct RecordingPlatform {
    inner: TestPlatform,
    screen: RecordingScreen,
}

impl Platform for RecordingPlatform {
    fn screen(&self) -> &dyn Screen {
        &self.screen
    }

    fn now(&self) -> Instant {
        self.inner.now()
    }

    fn database_repository(&self) -> &dyn DatabaseRepository {
        self.inner.database_repository()
    }

    fn filesystem(&self) -> &dyn Filesystem {
        self.inner.filesystem()
    }

    fn audio_sink(&self) -> Box<dyn AudioSink> {
        self.inner.audio_sink()
    }

    fn write_stdout(&self, data: &[u8]) {
        self.inner.write_stdout(data)
    }

    fn write_stderr(&self, data: &[u8]) {
        self.inner.write_stderr(data)
    }

    fn exit(&self) {
        self.inner.exit()
    }

    fn vibrate(&self, duration_ms: u64, intensity: u8) {
        self.inner.vibrate(duration_ms, intensity)
    }
}

fn tick_until(
    emulator: &mut LgtEmulator,
    limit: usize,
    condition: impl Fn() -> bool,
) -> Result<()> {
    for tick in 0..limit {
        if let Err(error) = emulator.tick() {
            eprintln!("libwipi-platformer-tick-failed tick={tick}");
            return Err(error);
        }
        if condition() {
            return Ok(());
        }
    }
    Ok(())
}

fn last_hash(screen: &ScreenStats) -> Option<u64> {
    screen.hashes.lock().unwrap().last().copied()
}

#[test]
fn libwipi_platformer_moves_and_jumps() -> Result<()> {
    let package = fs::read(env::var("LIBWIPI_PACKAGE").expect("LIBWIPI_PACKAGE is required"))
        .expect("read libwipi platformer package");
    let screen = Arc::new(ScreenStats::default());
    screen.width.store(320, Ordering::SeqCst);
    screen.height.store(240, Ordering::SeqCst);
    let platform = Box::new(RecordingPlatform {
        inner: TestPlatform::new(),
        screen: RecordingScreen(screen.clone()),
    });
    let mut emulator = LgtEmulator::from_archive(
        platform,
        extract_zip(&package)?,
        Options {
            enable_gdbserver: false,
            profile: None,
        },
    )?;

    tick_until(&mut emulator, 512, || {
        screen.paints.load(Ordering::SeqCst) >= 2
    })?;
    assert!(screen.paints.load(Ordering::SeqCst) >= 2, "timer did not repaint");
    assert!(screen.nonzero_bytes.load(Ordering::SeqCst) > 0, "frame is blank");
    let initial_hash = last_hash(&screen).expect("initial frame hash");

    emulator.handle_event(Event::Keydown(KeyCode::RIGHT));
    tick_until(&mut emulator, 256, || {
        last_hash(&screen).is_some_and(|hash| hash != initial_hash)
    })?;
    let moved_hash = last_hash(&screen).expect("moved frame hash");
    assert_ne!(moved_hash, initial_hash, "RIGHT did not move the player");
    emulator.handle_event(Event::Keyup(KeyCode::RIGHT));
    for _ in 0..24 {
        emulator.tick()?;
    }

    let grounded_hash = last_hash(&screen).expect("grounded frame hash");
    emulator.handle_event(Event::Keydown(KeyCode::OK));
    tick_until(&mut emulator, 256, || {
        last_hash(&screen).is_some_and(|hash| hash != grounded_hash)
    })?;
    emulator.handle_event(Event::Keyup(KeyCode::OK));
    let jumped_hash = last_hash(&screen).expect("jumped frame hash");
    assert_ne!(jumped_hash, grounded_hash, "OK did not start a jump");

    let hashes = screen.hashes.lock().unwrap();
    let mut unique_hashes = hashes.clone();
    unique_hashes.sort_unstable();
    unique_hashes.dedup();
    assert!(unique_hashes.len() >= 3, "gameplay produced too few visual states");
    println!(
        "libwipi-platformer-ok paints={} unique_frames={} size={}x{}",
        screen.paints.load(Ordering::SeqCst),
        unique_hashes.len(),
        screen.width.load(Ordering::SeqCst),
        screen.height.load(Ordering::SeqCst),
    );
    Ok(())
}
