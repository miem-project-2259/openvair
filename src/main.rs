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

mod tests {
    use crate::cmd_runner::CommandRunner;

    pub fn _get_runner() -> CommandRunner {
        CommandRunner
    }
}

mod cmd_runner {
    use std::process::{Command, ExitStatus, Output, Stdio};

    use anyhow::anyhow;
    pub struct CommandRunner;

    pub struct CommandResult {
        pub output: String,
        pub status: ExitStatus,
    }

    impl CommandResult {
        pub fn new(output: &str, status: &ExitStatus) -> Self {
            Self {
                output: output.to_string(),
                status: *status,
            }
        }
    }
    impl From<Output> for CommandResult {
        fn from(value: Output) -> Self {
            Self::new(
                &String::from_utf8(value.stdout)
                    .expect("invalid utf8 conversion in command output"),
                &value.status,
            )
        }
    }

    impl CommandRunner {
        pub fn try_pipe(
            &self,
            source: &mut Command,
            destination: &mut Command,
        ) -> anyhow::Result<CommandResult> {
            let source_child = source.stdout(Stdio::piped()).spawn()?;
            let source_out = source_child
                .stdout
                .ok_or(anyhow!("failed to get stdout of source in pipe"))?;
            let dst_child = destination
                .stdin(Stdio::from(source_out))
                .stdout(Stdio::piped())
                .spawn()?;
            let out = dst_child.wait_with_output()?;
            Ok(CommandResult::from(out))
        }

        pub fn try_run(&self, command: &mut Command) -> anyhow::Result<CommandResult> {
            Ok(CommandResult::from(
                command.stdout(Stdio::piped()).spawn()?.wait_with_output()?,
            ))
        }

        pub fn run(&self, command: &mut Command) -> CommandResult {
            self.try_run(command)
                .expect(&format!("failed to run command {command:?}"))
        }

        pub fn pipe(&self, source: &mut Command, destination: &mut Command) -> CommandResult {
            self.try_pipe(source, destination)
                .expect(&format!("pipe failed: {source:?} -> {destination:?}"))
        }
    }

    #[cfg(test)]
    mod tests {
        use crate::tests::_get_runner;

        use super::*;

        #[test]
        fn test_runner_run_command() {
            let runner = _get_runner();
            let mut cmd = Command::new("echo");
            let res = runner.run(cmd.arg("Hello world"));
            assert_eq!(res.output, String::from("Hello world\n"));
        }

        #[test]
        fn test_runner_pipe_commands() {
            let runner = _get_runner();
            let mut cmd_src = Command::new("echo");
            let mut cmd_sed = Command::new("sed");
            let res = runner.pipe(cmd_src.arg("Hello world"), cmd_sed.arg("s/world/me/"));
            assert_eq!(res.output, String::from("Hello me\n"));
        }
    }
}

mod pkg_management {
    use crate::cmd_runner::{CommandResult, CommandRunner};
    use std::process::Command;

    pub trait PackageProvider {
        fn try_check_installed(&self, package_name: &str) -> anyhow::Result<bool>;
        fn try_install(&self, package_name: &str) -> anyhow::Result<()>;
        fn check_installed(&self, package_name: &str) -> bool {
            self.try_check_installed(package_name)
                .expect(&format!("failed to check if {package_name} is installed"))
        }
        fn install(&self, package_name: &str) {
            self.try_install(package_name)
                .expect(&format!("failed to install {package_name}"))
        }
    }

    pub struct UbuntuPackageProvider<'a> {
        runner: &'a CommandRunner,
    }

    impl<'a> UbuntuPackageProvider<'a> {
        fn new(runner: &'a CommandRunner) -> Self {
            UbuntuPackageProvider { runner }
        }
    }

    impl PackageProvider for UbuntuPackageProvider<'_> {
        fn try_check_installed(&self, package_name: &str) -> anyhow::Result<bool> {
            let mut dpkg_cmd = Command::new("dpkg");
            let mut grep_cmd = Command::new("grep");

            let res = self
                .runner
                .try_pipe(dpkg_cmd.arg("-l"), grep_cmd.args(["-q", package_name]))?;

            return Ok(res.status.success());
        }

        fn try_install(&self, package_name: &str) -> anyhow::Result<()> {
            let mut sudo_cmd = Command::new("sudo");

            self.runner
                .try_run(sudo_cmd.args(["apt-get", "install", "-y", package_name]))?;
            Ok(())
        }
    }

    #[cfg(test)]
    mod tests {
        use crate::{
            pkg_management::{PackageProvider, UbuntuPackageProvider},
            tests::_get_runner,
        };

        #[cfg(feature = "ubuntu")]
        #[test]
        fn test_ubuntu_package_install() {
            let runner = _get_runner();
            let provider = UbuntuPackageProvider::new(&runner);

            let res = provider.try_install("hello");
            assert!(
                provider.check_installed("hello"),
                "failed to find installed hello package"
            );
            assert!(res.is_ok(), "expected install ok, got {:?}", res);
        }
    }
}

fn main() {
    println!("Hello, world!");
}
