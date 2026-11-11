# Organization

Read this before building or changing a sidebar, before writing a brief, before turning a project's
existing documents into a wiki, and before reviewing or organizing more than one page. It holds where a
wiki's structure comes from, what a section and a brief must hold, the placement test every page passes,
the tree review, and one product organized well and badly.

**A wiki can pass every check and still be organized wrongly.** `wiki check` reads sentences; it cannot
tell that a page sits under the wrong parent, that a section has lost its subject, or that the product's
main part has no page. Anyone who knows the product sees those errors in the sidebar at a glance, and
then stops trusting the pages under it. Structure is the writer's and the reviewer's judgment, and the
tests below are how that judgment is made.

The example is an invoicing application, chosen because most readers have seen one. Nothing about the
method changes for another product.

## Sources

**The structure comes from the product as a person meets it**, never from what was written or built
first. Read these before writing a brief, an intent or the sidebar, in this order:

1. **The product's own navigation**: its menus, sidebars, tabs and settings tabs. A product with no
   screens has one too: the commands its help lists, the resources its interface names, the topics of
   its own guide. The product's builders already grouped its parts for the people who use it, and those
   people look for a page under the same word.
2. **The product's own published copy**: its website, its README, a store listing, release notes. It
   states what the product is, who it is for and how its parts are grouped, in words that were approved
   to be published. **Published copy is a stated requirement**: a purpose, an audience or a grouping it
   gives is written without asking for it again. It is searched for in the repository before any of them
   is marked `{missing}`.
3. **The code**, for what each part does, and for the parts the navigation does not show: jobs, outside
   services, permissions.

These are not sources of structure, though each is worth reading for leads:

| Not a source of structure | Why |
|---|---|
| Existing documents, their headings and their order | They record what someone wrote down, and when. The part that never needed a document is usually the main one |
| Phases, milestones, tickets and release order | They are the order the work happened in, which a reader never meets |
| The code's folders and modules | They group by how the system is built. A person meets one feature that three folders build, and a wiki with one page per module is the source tree retold |
| The word budget | A page over its budget has an intent that is too broad. Text cut off the end of it to fit is not a subject |
| A settings screen | It groups by where a value is edited. A setting belongs on the page whose behavior it changes. A page for the settings screen lists its tabs and links the page each one changes, and states no behavior of its own |
| The teams that own each part | A reader does not know who owns what, and it changes |

Published copy says what the product is meant to be; the code says what it does. A sentence of behavior
still cites the code, and a claim the copy makes that no code carries out is written and marked
`{missing}`.

## Sections

A **section** is one group in the sidebar, declared in `wiki.toml`.

- **A section is one subject a person meets in the product**, named with the word the product uses for
  it. "Architecture", "Internals", "Phase two", "Other" and "Misc" name no subject a person meets.
  When the product calls a thing Notifications, neither the section nor the page is "Alerts".
- **Every page in a section is about that subject.** A page is tested against the section's name: a
  page about viewing files does not belong in a section named for a different part of the product,
  however near it sits on screen.
- **A section of one page is folded into its neighbor.** A sidebar of single-page sections is a list
  with extra headings. A section whose one page starts a branch of children is a section of that
  branch, and stands.
- **The sections, in order, lead a first-time reader** from what the system is for, to the parts a
  person uses most, to the parts they configure, to reference.

## Placement

**Run this test on every page**, when it is written, when it moves and in every review:

1. **It is a kind of its parent, or a part of it.** Say "*child* is a kind of *parent*" or "*child* is
   a part of *parent*" aloud. An invoice reminder is a part of invoices. A file viewer is neither a
   kind nor a part of a payments page, so it does not nest there.
2. **It sits in the section a reader would look in** when they know the product and not the wiki.
   Ask where the product itself shows the thing.
3. **No other page covers the same subject.** One concept is one page. When the product has one thing
   that comes in two kinds, such as an account that is either personal or shared, it is one page, or
   one parent with a page for each kind beneath it; it is never two unrelated pages in two sections.

- **A child page is a subject a reader would look for by name.** A page that holds what did not fit
  on its parent, such as "Adding and deleting" or "Other rules", fails the first test: it is a piece
  of the parent's text, not a part of the parent's subject.
- **Two pages with one title are read side by side.** Under different parents they can be two
  subjects, such as a size limit and a rate limit, or one subject written twice. One subject keeps one
  page, and the other page links to it.
- **A page for one member of a cross-cutting group states only what differs there.** A page for one
  platform or one plan links to the page that owns each subject, and never retells it.

A page that fails the first test moves. A page that fails the second moves, or its section is renamed
to the subject its pages share. Two pages that fail the third are merged, or one becomes the parent of
the other.

**A naming refusal is fixed by renaming the page, never by moving it.** When "Saved reports" under
**Reports** is reported for repeating its parent's word, the page becomes **Saved** and stays where it
is. Its place was decided by the placement test, and a warning about its name says nothing about its
place. Moving a page to quiet a warning leaves a page that passes the check under a parent it is not a
part of.

**A place is never chosen to satisfy a check.** The same holds for a budget, a family layout and a
broken link: fix what the check names, where the page already belongs.

## Subjects

**A page defines its subject by what it is and what sets it apart**, in the first sentence of its lead.

| Never | Because | Instead |
|---|---|---|
| "A payment provider is an entry a person keeps in Settings › Providers." | It says where the thing is edited. A reader still does not know what one is | "A payment provider is the outside service that charges a customer's card when an invoice is paid." |
| "Reminders are stored in the `reminders` table." | It says where the thing is kept | "A reminder is an email sent to a customer whose invoice is past due." |
| "Reports is the fourth tab." | It says where the thing is shown | "A report totals what was invoiced, paid and overdue across a period." |

Where a thing is set up, stored or shown is a fact about it, stated later on the page and in the
infobox. It is never the definition.

## Brief

The **brief** is the page that says what the product is, in one screen. A wiki has one, and it is
written before the sidebar, because the sidebar is the brief's scope drawn as a list.

- **Purpose**: what the product is and what it is for, from the published copy.
- **Users**: who it is for, named as the published copy names them. **Users is never left `{missing}`
  while the website, the README, a store listing or the release notes states it.** Search the
  repository for them first.
- **Scope**: the parts the product has, grouped as its navigation groups them, and what it leaves to
  other systems.
- **A brief invents nothing.** Where no published copy and no stated requirement gives a purpose, an
  audience or a boundary, that line is marked `{missing}` and asked for.

The brief describes no behavior, so the wiki marks it `goals = false` and it carries no citations; every
other page cites.

## Completeness

**A group lists every member the system has.** When the product builds for three platforms, supports
four providers or offers five plans, each has its page under one parent, as
[Page families](page-families.md) describes, and the parent's table has a row for each.

- **Count the members from the code and the published copy**, never from the pages or documents that
  exist: the build targets, the provider list, the supported list on the website.
- **A missing member is a coverage gap**, reported like any other behavior no page covers. The member
  most often missing is the main one, because it was built first and nothing was ever written about it.
- **A member not written yet gets a draft page** in the family's layout, or a row marked `{missing}`
  in the parent's table, so the gap shows.

## Tree review

**Review the tree before any page's content.** A review that opens the first page and starts reading
never sees the structure, and passes a wiki whose every page is true and whose sidebar is wrong.

1. **Read the sidebar alone**, as `wiki.toml` declares it: the section names, in order, and the pages
   each names. Set it beside the product's navigation and its published copy. Each part the product
   names has a section or a page; each section is one subject, as [Sections](#sections) requires.
2. **List every page's title and parent**, with a script and not by eye, and run the
   [placement test](#placement) on each one. Sort the list by title too, and read each pair of pages
   that share one.
3. **Check each group for completeness**, counting members from the code and the published copy.
4. **Read the first sentence of every lead**, and name each that defines its subject by where it is
   set up, stored or shown.
5. **Read the brief** against the published copy: purpose, users and scope are stated, and none is
   marked `{missing}` while the copy gives it.
6. **Report the tree's findings first**, before any finding about a page's content: the page or
   section, which test it fails, and the move, merge, rename or new page that fixes it.

`wiki families` helps with the second step: it names every nested title that repeats its parent's
word. Each such page is renamed where it is.

## Migration

Turning a project's existing documents into a wiki is not a conversion. **The old documents are leads:
they say what to look for in the code, and they decide nothing about the structure.**

1. Read the [sources](#sources): the navigation, the published copy, then the code.
2. Write the brief, and ask for its approval.
3. Build the sidebar from the product: one section for each subject a person meets, with the pages
   that start each branch. Ask for its approval before writing pages.
4. Map each old section onto that structure: the page it informs, or nowhere. Content about a phase, a
   plan, a decision record or how the code is laid out is engineering documentation and is left where
   it is.
5. List what the structure holds that no old document covers. Those pages are written from the code;
   they are usually the product's main parts.
6. Write each page from the code, by the page standard, citing the code and never the old document.
   A statement found only in an old document is a lead to check against the code, and is written only
   when the code or a stated requirement supports it.
7. Run the [tree review](#tree-review), then `wiki check`.

**An old heading is never mirrored.** A sidebar that reads like the old documents' table of contents
was converted, not organized.

---

## Done badly

The application's own menu reads Invoices, Customers, Payments, Reports, Settings. Its website says it
is "for freelancers who bill by the hour" and runs on the web, on iOS and on Android. Its old documents
are an architecture overview, a plan for "Phase 2: Android", and a settings reference.

```text
Start
  Home
  Brief                 Users: {missing}
Architecture
  Overview
  Data model
Phase 2
  Android
Settings
  Providers             "A payment provider is an entry a person keeps in Settings › Providers."
  Reminders
  Saved reports
Billing
  Invoices
    PDF viewer
  Personal accounts
Teams
  Shared accounts
```

Every page here can pass `wiki check`.

## Done well

```text
Start
  Home
  Brief                 Users: freelancers who bill by the hour
Invoices
  Invoices
    Reminders
  Customers
    Accounts            personal and shared, one page
Payments
  Payments
    Providers           one page for each provider the code supports
Reports
  Reports
    Saved
Platforms
  Platforms
    Web
    iOS
    Android
```

## Differences

**The sections are the product's own.** Invoices, Payments and Reports are the words on the
application's menu. "Architecture" and "Phase 2" were the old documents' headings, and no person using
the application meets either.

**The main platform has a page.** The old documents described Android because Android had a plan. The
web application, built first, had none, so the mirrored wiki left it out. Counting platforms from the
website found three.

**Users are stated.** The website said who the application is for; the brief repeats it instead of
marking it missing.

**A setting sits on the page it changes.** Reminders are a part of invoices, and providers a part of
payments. A Settings section grouped them by the screen they are edited on.

**The saved reports page was renamed, not moved.** It is **Saved**, under **Reports**. In the failed
version it was moved into Settings to clear a warning about its title.

**One concept is one page.** An account is personal or shared; the failed version split it across two
sections, and neither page said what an account is.

**The viewer left the place it did not belong.** A viewer for PDF files is neither a kind nor a part
of an invoice. It is described on the page for the thing a person opens with it, or gets a page where
the product shows it.

**A provider is defined by what it is.** "The outside service that charges a customer's card" tells
every reader what a provider is; "an entry in Settings" told them only where to click.

## Definition of done

1. The brief states purpose, users and scope from the published copy, and marks `{missing}` only what
   no source gives.
2. Every section is one subject a person meets in the product, and none holds one page with no
   children.
3. Every page passes the placement test: a kind or a part of its parent, in the section a reader would
   look in, and the only page on its subject.
4. Every group lists every member the code and the published copy name.
5. Every lead's first sentence says what its subject is.
6. No section, page or heading mirrors an old document, a phase or a folder of the code.
7. No page was moved to satisfy a check.
