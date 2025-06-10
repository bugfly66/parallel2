use std::env;
use std::fs::File;
use std::io::{self, Write};

fn main() -> io::Result<()> {
    let len = env::var("LEN").unwrap_or("1".to_string()); // 默认为100
    let mlen = env::var("MLEN").unwrap_or("1".to_string());
    println!("cargo:rerun-if-env-changed=LEN");
    println!("cargo:rerun-if-env-changed=MLEN");
    let mut file = File::create("src/len.rs")?;
    writeln!(file, "pub const LEN: usize = {};", len)?;
    writeln!(file, "pub const MLEN: usize = {};", mlen)?;
    // 显式flush以确保写入
    file.flush()?;
    cc::Build::new()
        .file("src/main.c") // 指定C源文件位置
        .flag_if_supported("-fopenmp") // 启用OpenMP支持
        .compile("csum"); // 生成的库名称
    println!("cargo:rustc-link-lib=static=csum");
    // 添加 OpenMP 链接支持
    if cfg!(target_os = "linux") {
        // 对于 gcc 和 clang 链接器
        println!("cargo:rustc-link-arg=-fopenmp");

        // 如果上面不行，尝试手动链接
        // println!("cargo:rustc-link-lib=gomp");
    } else if cfg!(target_os = "macos") {
        println!("cargo:rustc-link-lib=omp");
        // 如果使用 brew 安装的 libomp
        println!("cargo:rustc-link-search=native=/usr/local/opt/libomp/lib");
    }
    // Linux/Mac 需要链接数学库 libm
    if cfg!(target_os = "linux") || cfg!(target_os = "macos") {
        println!("cargo:rustc-link-lib=m");
    }
    Ok(())
}
