///! Модуль openvair_manager
///!
///! Данный модуль предназначен для инкапсуляции вспомогательных модулей,
///! использующихся в программе
pub mod cli;
pub mod installer;
pub mod node_exporter;
pub mod prometheus;
pub mod python;
pub mod services;

pub mod cmd_runner;
pub mod docker;
pub mod files;
pub mod git_pkg;
pub mod pkg_management;
pub mod project_config;
