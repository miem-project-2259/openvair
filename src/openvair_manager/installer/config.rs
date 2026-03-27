use std::process::Command;

use log::info;

use crate::{cmd_runner::CommandRunner, openvair_manager::cli::OpenvairManagerInstallArgs};

#[derive(Default, Clone, Debug)]
pub struct InstallerConfig {
    pub user: String,
    pub os: String,
    pub arch: String,
    pub project_name: String,
    pub docs_project_name: String,
    pub user_path: String,
    pub project_path: String,
    pub docs_project_path: String,
    pub project_config_file: String,
    pub dependencies_file: String,
    pub processor_type: String,
}

impl InstallerConfig {
    pub fn builder() -> InstallerConfigBuilder {
        InstallerConfigBuilder::new()
    }
}

#[derive(Clone, Debug)]
pub struct InstallerConfigBuilder {
    config: InstallerConfig,
}

impl<'a> InstallerConfigBuilder {
    pub fn new() -> Self {
        Self {
            config: Default::default(),
        }
    }

    pub fn build(
        mut self,
        runner: &'a CommandRunner,
        install_args: &'a OpenvairManagerInstallArgs,
    ) -> InstallerConfig {
        self.config.user = install_args.user.clone();
        self.config.os = runner
            .pipe(
                Command::new("lsb_release").arg("-i"),
                Command::new("awk").arg("'{print tolower($3)}'"),
            )
            .output;
        self.config.arch = runner.run(Command::new("uname").arg("-m")).output;
        self.config.project_name = install_args.project_name.clone();
        self.config.docs_project_name = install_args.docs_project_name.clone();
        self.config.user_path = format!("/opt/{}", self.config.user);
        self.config.project_path =
            format!("{}/{}", self.config.user_path, self.config.project_name);
        self.config.docs_project_path = format!(
            "{}/{}",
            self.config.user_path, self.config.docs_project_name
        );
        self.config.project_config_file =
            format!("{}/project_config.toml", self.config.project_path);
        self.config.dependencies_file =
            format!("{}/third_party_requirements.txt", self.config.project_path);

        if self.config.arch == "aarch64" {
            self.config.processor_type = "arm64".to_string();
        } else {
            self.config.processor_type = "amd64".to_string();
        }

        info!("architecture set to {}", self.config.arch);
        self.config
    }
}
