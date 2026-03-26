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

mod docker {
    pub mod provider {
        use std::process::Command;

        use crate::cmd_runner::CommandRunner;

        pub struct DockerProvider<'a> {
            pub runner: &'a CommandRunner,
        }

        impl<'a> DockerProvider<'a> {
            pub fn new(runner: &'a CommandRunner) -> DockerProvider<'a> {
                Self { runner }
            }
        }

        impl<'a> DockerProvider<'a> {
            fn try_run(&self) -> anyhow::Result<()> {
                todo!()
            }

            fn try_exec(&self, container_name: &str, command: &str) -> anyhow::Result<()> {
                let mut cmd = Command::new("sudo");
                self.runner.try_run(cmd.args([
                    "docker",
                    "exec",
                    "-it",
                    container_name,
                    command,
                ]))?;
                Ok(())
            }
        }
    }

    pub mod installer {}
}

fn main() {
    println!("Hello, world!");
}
