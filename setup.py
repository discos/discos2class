#!/usr/bin/env python
#coding=utf-8

#
#
#    Copyright (C) 2016  Marco Bartolini, bartolini@ira.inaf.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from distutils.core import setup
from distutils import dir_util
import os

setup(
      name = "discos2class",
      version = "0.3.1-beta",
      description = "convert discos fits to class format",
      author = "Marco Bartolini",
      author_email = "bartolini@ira.inaf.it",
      license = "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
      url = "http://github.com/discos/discos2class/",
      packages = ["discos2class",],
      package_dir = {"discos2class" : "src", },
      scripts = ["scripts/discos2class"],
     )

