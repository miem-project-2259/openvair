use command_macros::cmd;

#[derive(Clone, Debug)]
struct InstallerConfig {
    user: String,
    os: String,
    arch: String,
    project_name: String,
    docs_project_name: String,
    user_path: String,
    project_path: String,
    docs_project_path: String,
    project_config_file: String,
    dependencies_file: String,
}

mod tests;

mod cmd_runner;

mod pkg_management;

mod project_config;

mod docker;

fn main() {
    println!("Hello, world!");
}
