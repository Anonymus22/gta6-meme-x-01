// gta6-meme-x-01 entry program (Node 22, standard library only).
//
// The entry itself is a post on X: a GTA 6 meme whose picture carries
// make.fun's ghost, posted publicly with the entrant's play code in its
// text. This program has exactly one job -- to carry the post's address
// from the repository to the grader. It copies POST.json from the bot
// directory into the output directory, byte for byte, where the house
// reads it and fetches the post from X. Nothing else is written, and
// nothing about the post is judged from this program's output.
//
// Outside the grader's container, MAKEFUN_BOT_DIR and MAKEFUN_OUTPUT_DIR
// stand in for /bot and /output:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const botDir = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

function main() {
  const from = join(botDir, 'POST.json');
  const to = join(outputDir, 'POST.json');
  mkdirSync(outputDir, { recursive: true });
  try {
    copyFileSync(from, to);
  } catch (err) {
    // Fail loudly rather than leave the grader an empty output directory:
    // without POST.json the entry cannot be read at all.
    console.error(`could not copy ${from} to ${to}: ${(err as Error).message}`);
    process.exit(1);
  }
}

main();
