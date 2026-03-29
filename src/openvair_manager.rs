pub mod cli;
pub mod installer;
pub mod python;
pub mod services;
pub mod node_exporter {
    pub mod installer {
        use std::rc::Rc;

        use crate::cmd_runner::CommandRunner;

        pub trait NodeExporterInstaller {
            fn install_node_exporter(&self) -> anyhow::Result<()>;
        }

        #[derive(Clone, Debug)]
        pub struct UbuntuNodeExporterInstaller {
            runner: Rc<CommandRunner>,
            config: UbuntuNodeExporterInstallerConfig,
        }

        impl NodeExporterInstaller for UbuntuNodeExporterInstaller {
            fn install_node_exporter(&self) -> anyhow::Result<()> {
                todo!()
            }
        }

        #[derive(Clone, Debug, Default)]
        pub struct UbuntuNodeExporterInstallerConfig {
            version: String,
            proc: String,
        }

        impl UbuntuNodeExporterInstallerConfig {
            pub fn builder() -> UbuntuNodeExporterInstallerConfigBuilder {
                UbuntuNodeExporterInstallerConfigBuilder::default()
            }
        }

        #[derive(Clone, Debug, Default)]
        pub struct UbuntuNodeExporterInstallerConfigBuilder {
            config: UbuntuNodeExporterInstallerConfig,
        }

        impl UbuntuNodeExporterInstallerConfigBuilder {
            pub fn version(mut self, value: impl ToString) -> Self {
                self.config.version = value.to_string();
                self
            }

            pub fn proc(mut self, value: impl ToString) -> Self {
                self.config.proc = value.to_string();
                self
            }

            pub fn build(self) -> UbuntuNodeExporterInstallerConfig {
                self.config
            }
        }

        impl UbuntuNodeExporterInstaller {
            pub fn new(
                config: UbuntuNodeExporterInstallerConfig,
                runner: Rc<CommandRunner>,
            ) -> Self {
                Self { runner, config }
            }
        }
    }
}

mod files;
