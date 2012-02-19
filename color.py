#!/usr/bin/python -u
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 et sts=2 ai:

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(30, 38)

def red(l):
  return COLOR_SEQ % RED + l + RESET_SEQ

def yellow(l):
  return COLOR_SEQ % YELLOW + l + RESET_SEQ

def green(l):
  return COLOR_SEQ % GREEN + l + RESET_SEQ

if __name__ == "__main__":
  print red("red")
  print yellow("yellow")
  print green("green")
