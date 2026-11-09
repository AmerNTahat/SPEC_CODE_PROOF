# Source from any directory to select this workspace's isolated Rust/Verus tools.
# Does not install tools or change your global Rust configuration.
_scp_tools_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.scp-workbench/tools" && pwd)"
export CARGO_HOME="$_scp_tools_dir/rust/cargo"
export RUSTUP_HOME="$_scp_tools_dir/rust/rustup"
export RUSTUP_TOOLCHAIN=1.92.0
export PATH="$_scp_tools_dir/verus-0.2026.01.23.1650a05/verus-x86-linux:$CARGO_HOME/bin:$PATH"
unset _scp_tools_dir
