pub mod cli;
pub mod installer;
pub mod node_exporter;
pub mod prometheus {
    pub mod installer {
        use std::rc::Rc;

        use crate::{
            cmd_runner::CommandRunner,
            openvair_manager::{files::FilesProvider, git_pkg::GitPkgInstaller},
        };

        pub trait PrometheusInstaller {
            fn install_prometheus(&self) -> anyhow::Result<()>;
        }

        pub struct UbuntuPrometheusInstaller {
            runner: Rc<CommandRunner>,
            files: Rc<FilesProvider>,
            git_pkg: Rc<GitPkgInstaller>,
            config: UbuntuPrometheusInstallerConfig,
        }

        impl UbuntuPrometheusInstaller {
            pub fn new(
                runner: Rc<CommandRunner>,
                files: Rc<FilesProvider>,
                git_pkg: Rc<GitPkgInstaller>,
                config: UbuntuPrometheusInstallerConfig,
            ) -> Self {
                Self {
                    runner,
                    files,
                    git_pkg,
                    config,
                }
            }
        }

        pub struct UbuntuPrometheusInstallerConfig {
            proc: String,
            dependencies_file: String,
        }

        impl UbuntuPrometheusInstallerConfig {
            pub fn new(proc: String, dependencies_file: String) -> Self {
                Self {
                    proc,
                    dependencies_file,
                }
            }
        }
    }
}
pub mod python;
pub mod services;

pub mod files;
pub mod git_pkg;
