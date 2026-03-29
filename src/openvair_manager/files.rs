use std::{process::Command, rc::Rc};

use crate::cmd_runner::CommandRunner;

pub struct FilesProvider {
    runner: Rc<CommandRunner>,
}

impl FilesProvider {
    pub fn new(runner: Rc<CommandRunner>) -> Self {
        Self { runner }
    }

    pub fn remove_file(&self, path: &str) -> anyhow::Result<()> {
        self.runner
            .try_run(Command::new("sudo").args(["rm", path]))?;
        Ok(())
    }

    pub fn remove_dir(&self, path: &str) -> anyhow::Result<()> {
        self.runner
            .try_run(Command::new("sudo").args(["rm", "-rf", path]))?;
        Ok(())
    }

    pub fn mv(&self, src_path: &str, target_path: &str) -> anyhow::Result<()> {
        self.runner
            .try_run(Command::new("sudo").args(["mv", src_path, target_path]))?;
        Ok(())
    }

    pub fn cp(&self, src_paths: &[&str], target_path: &str) -> anyhow::Result<()> {
        let mut args = vec!["cp"];
        args.extend(src_paths);
        args.push(target_path);

        self.runner.try_run(Command::new("sudo").args(args))?;
        Ok(())
    }

    pub fn chown(&self, owner: &str, files: &[&str]) -> anyhow::Result<()> {
        let mut args = vec!["chown", "-R"];
        args.push(owner);
        args.extend(files);

        self.runner.try_run(Command::new("sudo").args(args))?;
        Ok(())
    }
}
