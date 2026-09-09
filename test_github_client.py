import asyncio

from mcp_gateway.github_client import (
    get_user,
    get_user_repositories,
)


async def main():
    username = "VedantLodhi"

    print("\nTEST 1 - GITHUB USER PROFILE")

    user = await get_user(username)

    print("Login       :", user.get("login"))
    print("Name        :", user.get("name"))
    print("Bio         :", user.get("bio"))
    print("Public Repos:", user.get("public_repos"))
    print("Followers   :", user.get("followers"))

    assert user.get("login") == username

    print("GitHub user profile PASSED.")


    print("\nTEST 2 - GITHUB REPOSITORIES")

    repos = await get_user_repositories(username)

    print("Repository Count:", len(repos))

    for repo in repos[:10]:
        print(
            f"- {repo.get('name')} | "
            f"{repo.get('language')} | "
            f"{repo.get('description')}"
        )

    assert isinstance(repos, list)
    assert len(repos) > 0

    print("GitHub repositories PASSED.")


if __name__ == "__main__":
    asyncio.run(main())