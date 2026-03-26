use std::process::Command;

use log::info;

use crate::{
    cmd_runner::CommandRunner,
    docker::{installer::DockerInstaller, provider::DockerProvider},
    openvair_manager::cli::{OpenvairManagerCli, OpenvairManagerInstallArgs},
    pkg_management::PackageProvider,
};

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
}

impl InstallerConfig {
    fn builder() -> InstallerConfigBuilder {
        InstallerConfigBuilder::new()
    }
}

#[derive(Clone, Debug)]
pub struct InstallerConfigBuilder {
    config: InstallerConfig,
}

impl<'a> InstallerConfigBuilder {
    fn new() -> Self {
        Self {
            config: Default::default(),
        }
    }

    fn build(
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
        self.config
    }
}

pub struct OpenvairInstallerService<'a> {
    config: InstallerConfig,
    pkg: &'a dyn PackageProvider,
    runner: &'a CommandRunner,
    docker_installer: &'a dyn DockerInstaller,
    docker: &'a DockerProvider<'a>,
}

impl<'a> OpenvairInstallerService<'a> {
    pub fn new(
        config: InstallerConfig,
        pkg: &'a dyn PackageProvider,
        runner: &'a CommandRunner,
        docker_installer: &'a dyn DockerInstaller,
        docker: &'a DockerProvider<'a>,
    ) -> Self {
        Self {
            config,
            pkg,
            runner,
            docker_installer,
            docker,
        }
    }

    pub fn install_openvair() {
        info!("starting openvair installation");
    }
}
