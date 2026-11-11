// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { execFileSync } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

/**
 * The vkg, serve and mcp stacks build linux/arm64 image assets. On an x86_64
 * host with no arm64 emulation the deploy fails ~20 minutes in with
 * `exec format error`; preflight-deploy.sh §3b catches that up front. Run its
 * bash detection functions against fixture input.
 */

const SCRIPT = path.join(
  __dirname,
  "..",
  "..",
  "scripts",
  "preflight-deploy.sh",
);

const IS_WINDOWS = process.platform === "win32";

/**
 * Which bash is on PATH, if any: "wsl" (Windows, but a Linux kernel),
 * "posix" (Linux CI, macOS, Git Bash) or null (no usable bash).
 */
function bashFlavor(): "wsl" | "posix" | null {
  try {
    const kernel = execFileSync("bash", ["-c", "uname -s"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    return IS_WINDOWS && kernel === "Linux" ? "wsl" : "posix";
  } catch {
    return null;
  }
}

const BASH = bashFlavor();

/**
 * WSL reaches Windows drives through /mnt/<letter>; without this translation
 * every fixture path is "no such file or directory" inside WSL.
 */
function toBashPath(p: string): string {
  if (BASH !== "wsl") return p;
  const m = /^([A-Za-z]):[\\/](.*)$/.exec(p);
  return m ? `/mnt/${m[1].toLowerCase()}/${m[2].replace(/\\/g, "/")}` : p;
}

// Read once, and normalise line endings: a checkout made with
// core.autocrlf=true used to reach bash as `function() {\r`, which does not
// parse. `.gitattributes` now pins *.sh to LF; this keeps stale checkouts green.
const SCRIPT_SOURCE = fs.readFileSync(SCRIPT, "utf8").replace(/\r\n/g, "\n");

/** The body of a bash function, lifted verbatim from the real script. */
function bashFunctionSource(fn: string): string {
  const match = new RegExp(`^${fn}\\(\\)[\\s\\S]*?^\\}`, "m").exec(SCRIPT_SOURCE);
  if (!match) {
    throw new Error(`preflight-arm64: ${fn}() not found in ${SCRIPT}`);
  }
  return match[0];
}

/**
 * WSL's bash.exe drops everything after the `-c` string (arguments, "$@"), so
 * the function cannot receive a fixture path on its command line. Run it from a
 * temporary script file instead: argv and stdin then behave as on Linux, where
 * CI runs this suite.
 */
function bashRunsScript(): boolean {
  if (BASH === null) return false;
  const probe = path.join(os.tmpdir(), `coa-preflight-probe-${process.pid}.sh`);
  try {
    fs.writeFileSync(probe, "#!/usr/bin/env bash\necho ok\n", "utf8");
    const out = execFileSync("bash", [toBashPath(probe)], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    });
    return out.trim() === "ok";
  } catch {
    return false;
  } finally {
    fs.rmSync(probe, { force: true });
  }
}

const BASH_USABLE = bashRunsScript();
if (!BASH_USABLE) {
  console.warn(
    `[preflight-arm64] no usable POSIX bash on PATH${BASH ? ` (${BASH})` : ""}. ` +
      "Install Git Bash or WSL to run this suite locally; CI runs it on " +
      "ubuntu-latest.",
  );
}
// Only skip where the suite is not expected to run (a developer Windows box).
// On Linux a missing bash is a real failure and must stay red.
const describeBash = BASH_USABLE || !IS_WINDOWS ? describe : describe.skip;

let callSeq = 0;

/** Exit status of a preflight bash function (0 = detected). */
function callBash(fn: string, args: string[], stdin = ""): number {
  const program = `#!/usr/bin/env bash\n${bashFunctionSource(fn)}\n${fn} "$@"\n`;
  const tmp = path.join(
    os.tmpdir(),
    `coa-preflight-${process.pid}-${callSeq++}.sh`,
  );
  fs.writeFileSync(tmp, program, "utf8");
  try {
    execFileSync("bash", [toBashPath(tmp), ...args.map(toBashPath)], {
      input: stdin,
      stdio: ["pipe", "pipe", "pipe"],
    });
    return 0;
  } catch (e: unknown) {
    // Not `instanceof Error`: child_process errors come from a different realm
    // than jest's sandboxed globals.
    if (
      typeof e === "object" &&
      e !== null &&
      "status" in e &&
      typeof e.status === "number"
    ) {
      return e.status;
    }
    throw e;
  } finally {
    fs.rmSync(tmp, { force: true });
  }
}

describeBash("_buildx_lists_runnable_arm64", () => {
  const header =
    "NAME/NODE       DRIVER/ENDPOINT             STATUS  BUILDKIT    PLATFORMS\n";

  it("rejects a stopped builder configured for linux/arm64* (field-reported host)", () => {
    // Verbatim from the x86_64 Amazon Linux 2023 host with no binfmt handler.
    const out =
      header +
      "arm64builder *  docker-container                                \n" +
      "  arm64builder0 unix:///var/run/docker.sock stopped             linux/arm64*\n" +
      "default         docker                                          \n" +
      "  default       default                     running v0.12.6-m.1 linux/amd64, linux/amd64/v2, linux/amd64/v3, linux/amd64/v4, linux/386\n";
    expect(callBash("_buildx_lists_runnable_arm64", [], out)).not.toBe(0);
  });

  it("rejects a running builder where arm64 is only configured (*)", () => {
    const out =
      header +
      "  b0 unix:///var/run/docker.sock running v0.12.6 linux/arm64*, linux/amd64\n";
    expect(callBash("_buildx_lists_runnable_arm64", [], out)).not.toBe(0);
  });

  it.each([
    "  default default running v0.12.6 linux/amd64, linux/arm64, linux/386\n",
    "  default default running v0.12.6 linux/amd64, linux/arm64\n",
    "  desktop-linux desktop-linux running v0.16.1 linux/amd64, linux/arm64/v8, linux/386\n",
  ])("accepts a running node that detected arm64: %s", (line) => {
    expect(callBash("_buildx_lists_runnable_arm64", [], header + line)).toBe(0);
  });

  it("rejects empty output (engine has no buildx)", () => {
    expect(callBash("_buildx_lists_runnable_arm64", [], "")).not.toBe(0);
  });
});

describeBash("_arm64_binfmt_registered", () => {
  let dir: string;
  beforeEach(() => {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "binfmt-"));
    // What /proc/sys/fs/binfmt_misc held on the failing host.
    fs.writeFileSync(path.join(dir, "register"), "");
    fs.writeFileSync(path.join(dir, "status"), "enabled\n");
    fs.writeFileSync(
      path.join(dir, "kshcomp"),
      "enabled\ninterpreter /bin/ksh\n",
    );
  });
  afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

  it("rejects a registry with no qemu-aarch64 handler", () => {
    expect(callBash("_arm64_binfmt_registered", [dir])).not.toBe(0);
  });

  it("rejects a disabled qemu-aarch64 handler", () => {
    fs.writeFileSync(
      path.join(dir, "qemu-aarch64"),
      "disabled\ninterpreter /usr/bin/qemu-aarch64\n",
    );
    expect(callBash("_arm64_binfmt_registered", [dir])).not.toBe(0);
  });

  it.each(["qemu-aarch64", "qemu-aarch64-static"])(
    "accepts an enabled %s handler",
    (name) => {
      fs.writeFileSync(
        path.join(dir, name),
        "enabled\ninterpreter /usr/bin/qemu-aarch64\nflags: POCF\n",
      );
      expect(callBash("_arm64_binfmt_registered", [dir])).toBe(0);
    },
  );
});
