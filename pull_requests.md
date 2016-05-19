# Pull Requests

## Using The Signed-Off-By Process
We have the same requirements for using the signed-off-by process
as the Linux kernel. In short, you need to include a signed-off-by tag
in every patch:

"Signed-off-by:" this is a developer's certification that he or she
has the right to submit the patch for inclusion into the project.
It is an agreement to the [Developer's Certificate of Origin](./DCOO.md).
**Code without a proper signoff cannot be merged into the mainline.**

You should use your real name and email address in the format below:

> Signed-off-by: Random J Developer random@developer.example.org

### How to add DCOO to every single commit automatically
It is easy to forget adding the DCOO to the end of every commit message.
Fortunately there is a nice way to do it automatically. Once you've cloned
the repository onto your local machine, you can add a `prepare-commit-msg`
hook in the `.git/hooks` directory like this:

```#!/usr/bin/env python

import sys

commit_msg_filepath = sys.argv[1]

with open(commit_msg_filepath, 'r+') as f:
    content = f.read()
    f.seek(0, 0)
    f.write('%s\n\nSigned-off-by: <Your Name> <Your Email>' % content)
```
