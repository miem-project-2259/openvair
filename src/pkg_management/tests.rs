#[cfg(feature = "ubuntu")]
use super::*;
use crate::tests::_get_runner;

#[test]
fn test_ubuntu_package_install() {
    let runner = _get_runner();
    let provider = UbuntuPackageProvider::new(&runner);

    let res = provider.try_install("hello");
    assert!(
        res.expect("failed to run install").status.success(),
        "process did not terminate successfully"
    );
    assert!(
        provider.check_installed("hello"),
        "failed to find installed hello package"
    );
}
