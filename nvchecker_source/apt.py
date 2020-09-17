# MIT licensed
# Copyright (c) 2020 Felix Yan <felixonmars@archlinux.org>, et al.

from nvchecker.api import session, GetVersionError

APT_RELEASE_URL = "%s/dists/%s/Release"
APT_PACKAGES_PATH = "%s/binary-%s/Packages%s"
APT_PACKAGES_URL = "%s/dists/%s/%s"
APT_PACKAGES_SUFFIX_PREFER = (".xz", ".gz", "")

async def get_url(url):
  res = await session.get(url)
  data = res.body

  if url.endswith(".xz"):
    import lzma
    data = lzma.decompress(data)
  elif url.endswith(".gz"):
    import gzip
    data = gzip.decompress(data)

  return data.decode('utf-8')

async def get_version(name, conf, *, cache, **kwargs):
  srcpkg = conf.get('srcpkg')
  pkg = conf.get('pkg')
  mirror = conf['mirror']
  suite = conf['suite']
  repo = conf.get('repo', 'main')
  arch = conf.get('arch', 'amd64')
  strip_release = conf.get('strip_release', False)

  if srcpkg and pkg:
    raise GetVersionError('Setting both srcpkg and pkg is ambigious')
  elif not srcpkg and not pkg:
    pkg = name

  apt_release = await cache.get(APT_RELEASE_URL % (mirror, suite), get_url)
  for suffix in APT_PACKAGES_SUFFIX_PREFER:
    packages_path = APT_PACKAGES_PATH % (repo, arch, suffix)
    if " " + packages_path in apt_release:
      break
  else:
    raise GetVersionError('Packages file not found in APT repository')

  apt_packages = await cache.get(APT_PACKAGES_URL % (mirror, suite, packages_path), get_url)

  pkg_found = False
  for line in apt_packages.split("\n"):
    if pkg and line == "Package: " + pkg:
      pkg_found = True
    if srcpkg and line == "Source: " + srcpkg:
      pkg_found = True
    if pkg_found and line.startswith("Version: "):
      version = line[9:]
      if strip_release:
        version = version.split("-")[0]
      return version

  raise GetVersionError('package not found in APT repository')
