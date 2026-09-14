+++
title = "wiki-builder"
subtitle = "a tool that renders markdown into a wiki, and refuses what makes documentation rot"
status = "approved"
goals = false
intent = """
The front page exists to send a reader to the part of the tool they came for, and to show on its first
screen that wiki-builder's own wiki is written with, built by and checked by the tool it describes.
"""
+++

**wiki-builder** turns markdown pages into a wiki, and then refuses the things that make
documentation stop being true. Every page here was written with it and passes its checks, so the wiki
describes the tool and demonstrates it.

The [brief](brief.md) says in one screen what the tool is, who it is for and what it refuses.
[Installation](installation.md) starts a wiki in a project, and two guides put it on the web, on
[GitHub](deployment-github.md) or [Cloudflare](deployment-cloudflare.md).

A person writes [pages](pages.md), and an agent learns to write them from the [skill](skill.md). The
build makes the [site](site.md), and the [local server](serving.md) shows it on this machine. The
[checks](checks.md) are the reason the tool exists, [continuous integration](continuous-integration.md) runs
them on every push, and the [commands](commands.md) show how to use it.

The [goals page](goals.md) collects what every part of the tool is for.
