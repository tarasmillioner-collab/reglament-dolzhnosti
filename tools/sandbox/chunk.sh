#!/bin/bash
# Print base64 chunk N (13500 chars, folded at 4500) of a file + META line with length and sha256[:16] of the file.
# Usage: chunk.sh <file> <N>
F="$1"; N=${2:-1}
B=$(base64 -w0 "$F"); L=${#B}; S=$(sha256sum "$F" | cut -c1-16)
echo "META $L $S chunk=$N of=$(( (L+13499)/13500 ))"
echo "${B:$(( (N-1)*13500 )):13500}" | fold -w 4500
