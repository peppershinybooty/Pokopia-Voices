# Pokopia-Voices
Pokemon speak! Pokemon say their spoken names rather than cries.
RECOMPIA ONLY CURRENTLY

## Black screen after loading a save

Versions up to 2.1 can hang on a black screen right after your save loads (the game keeps running, you just can't see anything). It doesn't happen every time, which made it hard to pin down.

The cause is two checksums inside the sound archive that the game checks while loading: an 8-byte tag in front of every compressed chunk, and a CRC32 at the start of every entry. The new voice banks still had the game's old values. 2.1.1 has them fixed and nothing else changed.

If you build voice banks yourself, run `tools/fix_fdata_checks.py` on your modded `0x05d525ae.fdata` before packing it into a .pkmod:

    python3 tools/fix_fdata_checks.py 0x05d525ae.fdata
