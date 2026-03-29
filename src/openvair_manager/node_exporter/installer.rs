use std::{process::Command, rc::Rc};

use crate::{
    cmd_runner::CommandRunner,
    openvair_manager::{
        files::FilesProvider,
        services::{ServiceProvider, SystemdServiceProvider},
    },
};

pub trait NodeExporterInstaller {
    fn install_node_exporter(&self) -> anyhow::Result<()>;
}

#[derive(Clone, Debug)]
pub struct UbuntuNodeExporterInstaller {
    runner: Rc<CommandRunner>,
    files: Rc<FilesProvider>,
    services: Rc<SystemdServiceProvider>,
    config: UbuntuNodeExporterInstallerConfig,
}

impl NodeExporterInstaller for UbuntuNodeExporterInstaller {
    fn install_node_exporter(&self) -> anyhow::Result<()> {
        let node_exporter_s = "node_exporter";
        let version = self
            .runner
            .try_pipe(
                Command::new("grep").args([
                    &format!("^{node_exporter_s}=="),
                    &self.config.dependencies_file,
                ]),
                Command::new("sed").arg(format!("s/^{node_exporter_s}==//")),
            )?
            .output;

        let product = format!("{node_exporter_s}-{version}.linux-{}", &self.config.proc);

        let target_file = format!("{product}.tar.gz");
        let target_url = format!(
            "https://github.com/prometheus/{node_exporter_s}/releases/download/v${version}/{target_file}",
        );

        // Download node_exporter
        self.runner
            .try_run(Command::new("curl").args(["-LO", &target_url]))?;
        self.runner
            .try_run(Command::new("sudo").args(["tar", "-xf", &target_file]))?;
        self.files
            .mv(&format!("{product}/{node_exporter_s}"), "/usr/local/bin")?;

        // Cleanup
        self.files.remove_files(&[&target_file])?;
        self.files.remove_dirs(&[&product])?;

        // Setup service
        self.services.add_service_from_content(
            "
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

StartLimitIntervalSec=500
StartLimitBurst=5

[Service]
User=aero
Group=aero
Type=simple
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/node_exporter \
  --collector.logind

[Install]
WantedBy=multi-user.target
                    "
            .trim(),
            "node_exporter.service",
        )?;
        self.services.enable_service("node_exporter.service")?;
        self.services.start_service("node_exporter.service")?;

        // Configure prometheus
        self.files.append(
            r#"
  - job_name: "node_exporter"
    static_configs:
      - targets: ["localhost:9100"]
                    "#
            .trim(),
            "/etc/prometheus/prometheus.yml",
        )?;
        self.runner.try_run(Command::new("promtool").args([
            "check",
            "config",
            "/etc/prometheus/prometheus.yml",
        ]))?;
        // Restart prometheus
        self.runner.try_run(Command::new("curl").args([
            "-X",
            "POST",
            "https://localhost:9090/-/reload",
            "--insecure",
        ]))?;
        Ok(())
    }
}

#[derive(Clone, Debug, Default)]
pub struct UbuntuNodeExporterInstallerConfig {
    proc: String,
    dependencies_file: String,
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
    pub fn proc(mut self, value: impl ToString) -> Self {
        self.config.proc = value.to_string();
        self
    }

    pub fn dependencies_file(mut self, value: impl ToString) -> Self {
        self.config.dependencies_file = value.to_string();
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
        files: Rc<FilesProvider>,
        services: Rc<SystemdServiceProvider>,
    ) -> Self {
        Self {
            runner,
            config,
            files,
            services,
        }
    }
}
