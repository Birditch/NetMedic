# NetMedic — Homebrew formula (tap-ready draft).
#
# Until netmedic is published to PyPI / homebrew-core, you can install
# it from the user tap:
#
#   brew tap birditch/netmedic https://github.com/Birditch/NetMedic
#   brew install netmedic
#
# After PyPI publication this formula will be replaced by a regular
# pip-source-based formula and the homebrew-core PR can be opened.
class Netmedic < Formula
  include Language::Python::Virtualenv

  desc "Cross-platform DNS / network connectivity doctor"
  homepage "https://github.com/Birditch/NetMedic"
  url "https://github.com/Birditch/NetMedic/archive/refs/tags/v1.0.1-beta.1.tar.gz"
  # Replace with `shasum -a 256 v1.0.1-beta.1.tar.gz` after the tag exists.
  sha256 "REPLACE_WITH_TAG_TARBALL_SHA256"
  license "MIT"
  version "1.0.1b1"
  head "https://github.com/Birditch/NetMedic.git", branch: "main"

  depends_on "python@3.12"

  # Resource pins generated with `pip-compile` against the project's
  # ``requirements.txt``. Maintainers should regenerate these alongside
  # every dependency floor bump.
  resource "dnspython" do
    url "https://files.pythonhosted.org/packages/source/d/dnspython/dnspython-2.8.0.tar.gz"
    sha256 "REPLACE_PER_RELEASE"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-15.0.0.tar.gz"
    sha256 "REPLACE_PER_RELEASE"
  end

  resource "typer" do
    url "https://files.pythonhosted.org/packages/source/t/typer/typer-0.25.1.tar.gz"
    sha256 "REPLACE_PER_RELEASE"
  end

  resource "httpx" do
    url "https://files.pythonhosted.org/packages/source/h/httpx/httpx-0.28.1.tar.gz"
    sha256 "REPLACE_PER_RELEASE"
  end

  resource "h2" do
    url "https://files.pythonhosted.org/packages/source/h/h2/h2-4.3.0.tar.gz"
    sha256 "REPLACE_PER_RELEASE"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    output = shell_output("#{bin}/netmedic --help")
    assert_match "NetMedic", output
    assert_match "Network Doctor", output

    nm_output = shell_output("#{bin}/nm --help")
    assert_match "NetMedic", nm_output
  end
end
