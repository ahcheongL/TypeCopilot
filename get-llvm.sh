#! /bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <llvm-version> <nproc>"
    echo "Example: $0 16 6"
    exit 1
fi

VERSION=$1
NPROC=$2

wget "https://github.com/llvm/llvm-project/releases/download/llvmorg-$VERSION.0.0/llvm-project-$VERSION.0.0.src.tar.xz"
tar xf "llvm-project-$VERSION.0.0.src.tar.xz"
mv "llvm-project-$VERSION.0.0.src" llvm-project-$VERSION
cd llvm-project-$VERSION

cmake -S llvm -B build -G 'Unix Makefiles' -DLLVM_ENABLE_PROJECTS='clang;lld' -DCMAKE_BUILD_TYPE=Release -DLLVM_USE_LINKER=gold
cmake --build ./build --parallel $NPROC