#!/usr/bin/env ruby

require 'fileutils'

def system cmd, *args
  print "==> ", cmd, " ", *args.join(' '), "\n"
  raise "error" unless Kernel.system cmd, *args
end

# Build starcheat
system 'python3', 'build.py', '-v'
# Run some tests
FileUtils.cd 'build'
system './starcheat.py', '-v' 
# ToDo: run some other unit test here
unless ENV['TRAVIS_BUILD_ID'].nil? || ENV['TRAVIS_SECURE_ENV_VARS'] == 'false' || "#{ENV['TRAVIS_BRANCH']}" !~ /^v?(\d)+(\.\d+)*$/
  # Build OS X .app
  FileUtils.mv '../mac/setup.py', '.'
  system 'python3', 'setup.py', 'py2app'
  system '/usr/local/opt/qt5/bin/macdeployqt', 'dist/starcheat.app', '-verbose=2'
  # Test OS X .app
  FileUtils.mv 'dist/starcheat.app', 'StarCheat.app'
  system 'StarCheat.app/Contents/MacOS/starcheat', '-v'
  # Upload OS X .app to Github Releases
  system 'tar', 'czf', 'starcheat.tar.gz', 'StarCheat.app'
  puts '==> Uploading'
  `curl -H "Authorization: token #{ENV['GITHUB_KEY']}" -H "Accept: application/json" -d '{"tag_name":"#{ENV['TRAVIS_BRANCH']}","name":"starcheat #{ENV['TRAVIS_BRANCH']}"}' https://api.github.com/repos/wizzomafizzo/starcheat/releases` =~ /.*"upload_url":\s*"([\w\.\:\/]*){\?name}.*/m
  `curl -H "Authorization: token #{ENV['GITHUB_KEY']}" -H "Accept: application/json" -H "Content-Type: application/gzip" --data-binary @starcheat.tar.gz #{$1}?name=starcheat-#{ENV['TRAVIS_BRANCH']}-osx.tar.gz` unless $1.nil?
  raise "Skipping uploading build because tag is already in use" if $1.nil?
end
