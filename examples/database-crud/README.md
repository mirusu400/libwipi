# Database CRUD

This original WIPI-C clet exercises all 13 `MC_db*` APIs through the
`1.2.1/lgt-raptor/aram-raptor` synthetic emulator contract.

The first launch creates a fixed-size record database, inserts, selects,
updates, lists, sorts, and deletes records. It leaves two checked records in
place. A second launch reads those records before running another CRUD cycle
and lists the database catalog, which gives the ARAM test runner a distinct
restart-persistence assertion.

The application shows `DATABASE CRUD PASS` only when every return value,
record value, record ID list, sort order, and metadata check succeeds.

Build with the repository toolchain image:

```sh
make -C examples/database-crud package inspect
```

This is emulator evidence only. It is not a claim about a carrier database
provider or a physical handset.
