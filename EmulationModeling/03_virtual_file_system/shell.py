
from fs import VirtualFileSystem


def main():
    vfs = VirtualFileSystem()
    print("Virtual File System initialized. Type 'help' for commands.")

    while True:
        try:
            cwd = vfs.pwd()
            command_line = input(f"[{cwd}] $ ").strip()
            if not command_line:
                continue

            parts = command_line.split()
            cmd = parts[0]
            args = parts[1:]

            if cmd == "exit":
                break
            elif cmd == "help":
                print("Commands: ls, mkdir, touch, cd, pwd, cat, rm, save, load, exit")
            elif cmd == "ls":
                path = args[0] if args else None
                print(vfs.ls(path))
            elif cmd == "mkdir":
                if args:
                    print(vfs.mkdir(args[0]))
                else:
                    print("Usage: mkdir <path>")
            elif cmd == "touch":
                if len(args) >= 1:
                    content = " ".join(args[1:]) if len(args) > 1 else ""
                    print(vfs.touch(args[0], content))
                else:
                    print("Usage: touch <path> [content]")
            elif cmd == "cd":
                if args:
                    res = vfs.cd(args[0])
                    if res:
                        print(res)
                else:
                    print("Usage: cd <path>")
            elif cmd == "pwd":
                print(vfs.pwd())
            elif cmd == "cat":
                if args:
                    print(vfs.cat(args[0]))
                else:
                    print("Usage: cat <path>")
            elif cmd == "rm":
                if args:
                    print(vfs.rm(args[0]))
                else:
                    print("Usage: rm <path>")
            elif cmd == "save":
                path = args[0] if args else "vfs_state.json"
                print(vfs.save_state(path))
            elif cmd == "load":
                path = args[0] if args else "vfs_state.json"
                print(vfs.load_state(path))
            else:
                print(f"Unknown command: {cmd}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
