import subprocess
import os
import sys


def get_llvm(version, workspace):
    llvm_dir = f"llvm-project-{version}"

    if os.path.exists(os.path.join(workspace, llvm_dir)):
        print(f"llvm-project-{version} already exists")
        return

    url = f"https://github.com/llvm/llvm-project/releases/download/llvmorg-{version}.0.6/llvm-project-{version}.0.6.src.tar.xz"
    subprocess.run(f"wget {url}", shell=True, cwd=workspace)
    subprocess.run(
        f"tar xf llvm-project-{version}.0.6.src.tar.xz", shell=True, cwd=workspace
    )
    subprocess.run(
        f"mv llvm-project-{version}.0.6.src llvm-project-{version}",
        shell=True,
        cwd=workspace,
    )
    subprocess.run(
        f"rm llvm-project-{version}.0.6.src.tar.xz", shell=True, cwd=workspace
    )


def compile_llvm(version, nproc, workspace):
    llvm_dir = f"llvm-project-{version}"
    build_dir = os.path.join(workspace, llvm_dir, "build")

    if os.path.exists(build_dir):
        return

    subprocess.run(
        f"cmake -S llvm -B build -G 'Unix Makefiles' -DLLVM_ENABLE_PROJECTS='clang;lld' -DCMAKE_BUILD_TYPE=Debug -DLLVM_USE_LINKER=gold",
        shell=True,
        cwd=os.path.join(workspace, llvm_dir),
    )
    subprocess.run(
        f"cmake --build ./build --parallel {nproc}", shell=True, cwd=os.path.join(workspace, llvm_dir)
    )


if __name__ == "__main__":
    workspace = "/root"

    if len(sys.argv) < 3:
        print("Usage: python3 llvm.py <command> <version> [nproc]")
        print("Commands:")
        print("  get <version>      - Download LLVM version")
        print("  build <version> <nproc> - Compile LLVM version using nproc cores")
        sys.exit(1)

    command = sys.argv[1]
    version = sys.argv[2]

    if command == "get":
        get_llvm(version, workspace)
    elif command == "build":
        if len(sys.argv) < 4:
            print("Error: build command requires nproc argument")
            sys.exit(1)
        nproc = sys.argv[3]
        compile_llvm(version, nproc, workspace)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
