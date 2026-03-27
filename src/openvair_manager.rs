pub mod cli;
pub mod installer;
pub mod python {
    use std::process::Command;

    use crate::cmd_runner::CommandRunner;

    #[derive(Clone, Debug)]
    pub struct PythonProvider<'a> {
        runner: &'a CommandRunner,
        venv_path: String,
    }

    impl<'a> PythonProvider<'a> {
        pub fn new(runner: &'a CommandRunner, venv_path: String) -> Self {
            Self { runner, venv_path }
        }

        pub fn install(&self, package_name: &str) -> anyhow::Result<()> {
            self.runner.try_run(
                Command::new(format!("{}/bin/python3", self.venv_path)).args([
                    "-m",
                    "pip",
                    "install",
                    package_name,
                ]),
            )?;

            Ok(())
        }
    }
}
