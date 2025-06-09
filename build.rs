use std::env;
use std::fs::File;
use std::io::{self, Write};

fn main() -> io::Result<()> {
    let len = env::var("LEN").unwrap_or("100".to_string()); // 默认为100
    let mut file = File::create("src/len.rs")?;
    writeln!(file, "pub const LEN: usize = {};", len)?;
    Ok(())
}

