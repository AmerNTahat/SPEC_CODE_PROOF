# Optional: source after selecting an existing compatible Sireum installation.
# No installation and no changes to global Rust configuration.
if [ -n "${SIREUM_HOME:-}" ]; then
  export SIREUM_BIN="$SIREUM_HOME/bin/sireum"
  export PATH="$SIREUM_HOME/bin:$PATH"
fi
# Explicit profile sireum/sireum_sha256 fields select the checked tool identity.
