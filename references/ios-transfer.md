# iOS Mod transfer

Use this procedure only when the user asks to install or test a Mod on the Unciv iOS app.

1. If the Mod has images, finish image packing and full asset validation first. See [mod-authoring-reference.md](mod-authoring-reference.md).
2. On the phone, open **Mods → Receive Mod**. Use the displayed HTTP address and one-time six-digit code. Keep the phone and computer on the same Wi-Fi network.
3. Run the helper with the receiver's base URL and code:

   ```bash
   python3 <skill-directory>/scripts/unciv_mod.py upload <mod-folder> --receiver-url <displayed-address> --access-code <six-digit-code>
   ```

   The helper accepts the receiver's private-network or localhost IPv4 address. If the default ZIP already exists, choose a different unused path outside the Mod folder with `--output <zip-path>`; the helper does not overwrite an existing ZIP.
4. Keep the deterministic ZIP as a local artifact and record the SHA-256 printed by the helper together with the receiver's HTTP status and response. A successful upload confirms transfer only. Test behavior by starting a new game with the Mod enabled. Closing the receiver screen stops its local server.
5. Bind the installed ZIP, final preflight report, and simulator screenshots in `verification.json` with their SHA-256 digests. Record passed, failed, and unexercised checks separately; a recovered application crash remains a failed stability check.
