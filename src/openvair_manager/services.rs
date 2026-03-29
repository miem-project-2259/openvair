use std::{process::Command, rc::Rc};

use crate::cmd_runner::CommandRunner;

pub trait ServiceProvider {
    fn restart_service(&self, name: &str) -> anyhow::Result<()>;
    fn add_service_from_file(&self, file: &str) -> anyhow::Result<()>;
    fn enable_service(&self, name: &str) -> anyhow::Result<()>;
    fn start_service(&self, name: &str) -> anyhow::Result<()>;
}

pub struct SystemdServiceProvider {
    runner: Rc<CommandRunner>,
}

impl SystemdServiceProvider {
    pub fn new(runner: Rc<CommandRunner>) -> Self {
        Self { runner }
    }
}

impl ServiceProvider for SystemdServiceProvider {
    fn restart_service(&self, name: impl AsRef<str>) -> anyhow::Result<()> {
        self.runner
            .try_run(Command::new("sudo").args(["systemctl", "restart", name.as_ref()]))?;
        Ok(())
    }

    fn add_service_from_file(&self, file: impl AsRef<str>) -> anyhow::Result<()> {
        self.runner.try_run(Command::new("sudo").args([
            "cp",
            file.as_ref(),
            "/etc/systemd/system",
        ]))?;
        Ok(())
    }

    fn enable_service(&self, name: impl AsRef<str>) -> anyhow::Result<()> {
        self.runner
            .try_run(Command::new("sudo").args(["systemctl", "enable", name.as_ref()]))?;
        Ok(())
    }

    fn start_service(&self, name: impl AsRef<str>) -> anyhow::Result<()> {
        self.runner
            .try_run(Command::new("sudo").args(["systemctl", "start", name.as_ref()]))?;
        Ok(())
    }
}
