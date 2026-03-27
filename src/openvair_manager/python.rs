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

    fn install_cmd(&self) -> Command {
        Command::new(format!("{}/bin/python3", self.venv_path))
    }

    fn install_args() -> Vec<String> {
        vec![
            String::from("-m"),
            String::from("pip"),
            String::from("install"),
        ]
    }

    pub fn install(&self, package_name: &str) -> anyhow::Result<()> {
        let mut args = Self::install_args();
        args.push(package_name.to_string());
        self.runner.try_run(self.install_cmd().args(args))?;

        Ok(())
    }

    pub fn install_requirements(&self, requirements_path: &str) -> anyhow::Result<()> {
        let mut args = Self::install_args();
        args.extend([String::from("-r"), requirements_path.to_string()]);
        self.runner.try_run(self.install_cmd().args(args))?;

        Ok(())
    }
}
