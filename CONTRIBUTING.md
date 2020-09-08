# Contributing

Anyone is welcome to help with development of this package.
 Feel free to get in touch with other community members on IRC, the
mailing list or through issues here on GitHub.

- IRC: `#sync` on `irc.mozilla.org`
- Mailing list: <https://mail.mozilla.org/listinfo/sync-dev>
- and of course, [the issues list](https://github.com/mozilla-services/syncserver/issues)

## Bug Reports ##

You can file issues here on GitHub. Please try to include as much information as you can and under what conditions
you saw the issue.

## Sending Pull Requests ##

Patches should be submitted as pull requests (PR).

Before submitting a PR:
- Your code must run and pass all the automated tests before you submit your PR for review. "Work in progress" pull requests are allowed to be submitted, but should be clearly labeled as such and should not be merged until all tests pass and the code has been reviewed.
  - Run `make test` to make sure your code passes linting and all tests still pass.
- Your patch should include new tests that cover your changes. It is your and your reviewer's responsibility to ensure your patch includes adequate tests.

When submitting a PR:
- You agree to license your code under the project's open source license ([MPL 2.0](/LICENSE)).
- Base your branch off the current `master` (see below for an example workflow).
- Add both your code and new tests if relevant.
- Run `make test` to make sure your code passes linting and tests.
- Please do not include merge commits in pull requests; include only commits with the new relevant code.

See the main [README.md](/README.md) for information on prerequisites, installing, running and testing.

## Code Review ##

This project is subject to Mozilla's [engineering practices and quality standards](https://developer.mozilla.org/en-US/docs/Mozilla/Developer_guide/Committing_Rules_and_Responsibilities). Every patch must be peer reviewed. This project is part of the [Firefox Accounts module](https://wiki.mozilla.org/Modules/Other#Firefox_Accounts), and your patch must be reviewed by one of the listed module owners or peers.

## Example Workflow ##

This is an example workflow to make it easier to submit Pull Requests. Imagine your username is `user1`:

1. Fork this repository via the GitHub interface

2. The clone the upstream (as origin) and add your own repo as a remote:

    ```sh
    $ git clone https://github.com/mozilla-services/syncserver.git
    $ cd syncserver-auth-server
    $ git remote add user1 git@github.com:user1/syncserver.git
    ```

3. Create a branch for your fix/feature and make sure it's your currently checked-out branch:

    ```sh
    $ git checkout -b add-new-feature
    ```

4. Add/fix code, add tests then commit and push this branch to your repo:

    ```sh
    $ git add <files...>
    $ git commit
    $ git push user1 add-new-feature
    ```

5. From the GitHub interface for your repo, click the `Review Changes and Pull Request` which appears next to your new branch.

6. Click `Send pull request`.

### Keeping up to Date ###

The main reason for creating a new branch for each feature or fix is so that you can track master correctly. If you need
to fetch the latest code for a new fix, try the following:

```sh
$ git checkout master
$ git pull
```

Now you're ready to branch again for your new feature (from step 3 above).
