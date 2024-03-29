# Use UBI 8 as the base image
FROM registry.access.redhat.com/ubi8/ubi:latest

# Install development tools
RUN dnf groupinstall -y "Development Tools" && \
    dnf install -y cmake git python3-devel libxml2-devel ncurses-devel libedit-devel swig gcc-c++ && \
    dnf clean all

# Clone the LLVM project
RUN git clone https://github.com/llvm/llvm-project.git

# Create a build directory
WORKDIR /llvm-project/build

# Configure the build with CMake
RUN cmake -G "Unix Makefiles" \
    -DLLVM_ENABLE_PROJECTS=clang \
    -DCMAKE_BUILD_TYPE=Release \
    ../llvm

# Build LLVM and Clang
RUN make -j$(nproc)

# Install LLVM and Clang
RUN make install

# Set the path to include LLVM and Clang
ENV PATH="/usr/local/bin:${PATH}"

# Default command: Run tests
CMD ["sh", "-c", "cd /llvm-project/build && make test"]
