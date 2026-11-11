+++
title = "Organization"
subtitle = "the sources of a sidebar, sections, the placement test, page families, the brief, the tree review and migration"
status = "draft"
intent = """
The organization rules exist so that an agent derives a wiki's structure from the product as a person
meets it, places every page by what it is, and checks the whole tree before it calls a wiki organized.
A wiki whose every page passes the check while its sidebar is wrong leaves the product owner to find
each structural error by hand, which is the reading the wiki exists to save.
"""

[[infobox]]
group = "Identity"
rows = [
  { label = "Reference", value = "organization.md", cite = "sources" },
  { label = "Tasks", value = "Review, Organization, Migration", cite = "tree" },
]

[[infobox]]
group = "Rules"
rows = [
  { label = "Structure", value = "from the product's navigation and published copy", cite = "sources" },
  { label = "Placement", value = "a kind or a part of its parent, in the section a reader looks in, one page a subject", cite = "placement" },
  { label = "Naming refusal", value = "renamed, never moved", cite = "rename" },
  { label = "Review order", value = "the tree before any page", cite = "tree" },
]
+++

The skill's **organization** rules decide a wiki's sidebar, its sections and each page's place from what
the product is, because every check can pass on a wiki that is organized wrongly.[^sources] 
## Sources

**The structure comes from the product as a person meets it**: its own navigation, such as menus, sidebars,
settings tabs and the commands its help lists, and its own published copy.[^sources] It never comes from
existing documents, phases, the code's folders, a settings screen or the word budget.[^sources] The
product's website, README, store listing and release notes count as stated requirements, read before a
brief, an intent or the sidebar is written.[^sources]

## Brief

The brief states purpose, users and scope from the published copy, and is written before the
sidebar.[^brief] Users is never left `{missing}` while the published copy says who the product is
for.[^brief] The first sentence of a lead says what its subject is and what sets it apart, never where it
is set up, stored or shown.[^subject]

## Sections

A section is one subject a person meets in the product, named with the product's word for it, and every
page in it is about that subject.[^sections] A section of one page is folded into its neighbor, unless
that page starts a branch of children.[^sections]

## Placement

**Every page passes the placement test**: it is a kind of, or a part of, its parent; it sits in the
section a reader would look in; and no other page covers the same subject.[^placement] A title that
repeats its parent's word is fixed by renaming the page where it is, and a page is never placed, moved or
split to satisfy a check.[^rename]

## Page families

**Pages about things of one kind share one layout**: the same headings in the same order and the same
infobox labels, under a parent page that lists and compares them.[^families] A family has a page for every
member the system has, counted from the code and the published copy, and a member with no page is a
coverage gap.[^complete]

## Tree review

The Review and Organization tasks begin with the tree: the sidebar alone against the product, then every
page's title and parent with the placement test run on each, before any page's content.[^tree] The
Migration task reads a project's existing documents as leads only, builds the sidebar from the product,
then maps each old section onto it, and never mirrors an old heading.[^migration]

[^sources]: `src/skill/SKILL.md` — the Organization section, whose first two rules name the product's
    navigation and published copy; `src/skill/references/organization.md` — the opening paragraphs and the
    Sources section, whose table lists what is not a source of structure.
[^brief]: `src/skill/SKILL.md` — the third rule of the Organization section;
    `src/skill/references/organization.md` — the Brief section.
[^subject]: `src/skill/SKILL.md` — the second rule of the Page shape section;
    `src/skill/references/organization.md` — the Subjects section.
[^sections]: `src/skill/SKILL.md` — the fourth rule of the Organization section;
    `src/skill/references/organization.md` — the Sections section.
[^placement]: `src/skill/SKILL.md` — the fifth rule of the Organization section;
    `src/skill/references/organization.md` — the Placement section's three tests.
[^rename]: `src/skill/SKILL.md` — the sixth rule of the Organization section;
    `src/skill/references/organization.md` — the Placement section, where a place is never chosen to satisfy
    a check; `src/builder/build.py` — `families_report()` says to rename such a page under its parent.
[^families]: `src/skill/SKILL.md` — the Page families section; `src/skill/references/page-families.md` —
    the layout rules, the parent page, and a family done well and badly.
[^complete]: `src/skill/SKILL.md` — the last rule of the Organization section and the Page families rule
    that a family is complete; `src/skill/references/page-families.md` — the Families section.
[^tree]: `src/skill/SKILL.md` — the second step of the Review task and of the Organization task;
    `src/skill/references/organization.md` — the Tree review section.
[^migration]: `src/skill/SKILL.md` — the Migration task; `src/skill/references/organization.md` — the
    Migration section.
