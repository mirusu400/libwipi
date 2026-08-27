use std::{
    env, fs,
    sync::{
        Arc, Mutex,
        atomic::{AtomicU32, AtomicU64, AtomicUsize, Ordering},
    },
};

use test_utils::TestPlatform;
use wie_backend::{
    AudioCommand, AudioSink, DatabaseRepository, Emulator, Event, Filesystem,
    Instant, KeyCode, Options, Platform, Screen, canvas::Image, extract_zip,
};
use wie_lgt::LgtEmulator;
use wie_util::Result;

#[derive(Default)]
struct ScreenStats {
    paints: AtomicUsize,
    redraws: AtomicUsize,
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
        self.0.redraws.fetch_add(1, Ordering::SeqCst);
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
        if paint <= 3 {
            println!("libwipi-wie-frame paint={paint} hash={hash:016x} nonzero={nonzero}");
        }
    }

    fn width(&self) -> u32 {
        self.0.width.load(Ordering::SeqCst)
    }

    fn height(&self) -> u32 {
        self.0.height.load(Ordering::SeqCst)
    }
}

#[derive(Default)]
struct AudioStats {
    plays: AtomicUsize,
    stops: AtomicUsize,
    events: AtomicUsize,
    duration_ms: AtomicU64,
}

struct RecordingAudioSink(Arc<AudioStats>);

impl AudioSink for RecordingAudioSink {
    fn send(&self, command: AudioCommand) {
        match command {
            AudioCommand::Play { sequence, .. } => {
                println!(
                    "libwipi-wie-audio events={} duration_ms={}",
                    sequence.events.len(),
                    sequence.duration,
                );
                self.0.events.fetch_add(sequence.events.len(), Ordering::SeqCst);
                self.0.duration_ms.fetch_add(sequence.duration, Ordering::SeqCst);
                self.0.plays.fetch_add(1, Ordering::SeqCst);
            }
            AudioCommand::Stop { .. } => {
                self.0.stops.fetch_add(1, Ordering::SeqCst);
            }
        }
    }
}

struct RecordingPlatform {
    inner: TestPlatform,
    screen: RecordingScreen,
    audio: Arc<AudioStats>,
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
        Box::new(RecordingAudioSink(self.audio.clone()))
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
            eprintln!("libwipi-wie-tick-failed tick={tick}");
            return Err(error);
        }
        if condition() {
            return Ok(());
        }
    }
    Ok(())
}

#[test]
fn libwipi_conformance_runs_graphics_timer_input_and_audio() -> Result<()> {
    let package = fs::read(env::var("LIBWIPI_PACKAGE").expect("LIBWIPI_PACKAGE is required"))
        .expect("read libwipi conformance package");
    let screen = Arc::new(ScreenStats::default());
    screen.width.store(320, Ordering::SeqCst);
    screen.height.store(240, Ordering::SeqCst);
    let audio = Arc::new(AudioStats::default());
    let platform = Box::new(RecordingPlatform {
        inner: TestPlatform::new(),
        screen: RecordingScreen(screen.clone()),
        audio: audio.clone(),
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
    let paints_before_input = screen.paints.load(Ordering::SeqCst);
    assert!(paints_before_input >= 2, "timer did not produce a second frame");
    assert!(screen.nonzero_bytes.load(Ordering::SeqCst) > 0, "frame is blank");
    assert!(audio.events.load(Ordering::SeqCst) > 0, "SMAF produced no events");
    assert!(audio.duration_ms.load(Ordering::SeqCst) > 0, "audio has no duration");

    emulator.handle_event(Event::Keydown(KeyCode::OK));
    tick_until(&mut emulator, 256, || {
        screen.paints.load(Ordering::SeqCst) > paints_before_input
    })?;
    emulator.handle_event(Event::Keyup(KeyCode::OK));
    for _ in 0..32 {
        emulator.tick()?;
    }

    let paints = screen.paints.load(Ordering::SeqCst);
    let plays = audio.plays.load(Ordering::SeqCst);
    let hashes = screen.hashes.lock().unwrap();
    let mut unique_hashes = hashes.clone();
    unique_hashes.sort_unstable();
    unique_hashes.dedup();
    assert!(paints > paints_before_input, "input did not repaint the application");
    assert!(plays >= 2, "input did not replay the audio clip");
    assert!(unique_hashes.len() >= 2, "timer/input state never changed the frame");

    println!(
        "libwipi-wie-ok paints={paints} unique_frames={} plays={plays} audio_events={} duration_ms={} size={}x{}",
        unique_hashes.len(),
        audio.events.load(Ordering::SeqCst),
        audio.duration_ms.load(Ordering::SeqCst),
        screen.width.load(Ordering::SeqCst),
        screen.height.load(Ordering::SeqCst),
    );
    Ok(())
}
