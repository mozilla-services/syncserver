if [ ! -d "syncstorage-rs" ]; then
	echo "Downloading syncstorage-rs"
	git clone https://github.com/mozilla-services/syncstorage-rs
fi

echo "Starting syncstorage-rs"

cd syncstorage-rs

SYNC_HUMAN_LOGS=1 RUST_LOG=trace cargo run
