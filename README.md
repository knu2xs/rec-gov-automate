# rec-gov-automate

Automate tasks when interacting with Recreation.gov

## Getting Started

1 - Clone this repo.

2 - Create an environment with the requirements.
    
```
make env
```

## References

### Campground Identifiers

* 232464 - Klaloch
* 232094 - Salmon la Sac
* 233877 - La Wis Wis
* 232857 - Adams Fork
* 232860 - Walupt Lake
* 251906 - Sol Duc
* 259084 - Fairholme
* 232853 - Iron Creek

## Playwright

### Run Codegen

```
playwright codegen recreation.gov
```

## BumpVersion Cliff Notes

[Bump2Version](https://github.com/c4urself/bump2version) is preconfigured based on hints from [this article on Medium](https://williamhayes.medium.com/versioning-using-bumpversion-4d13c914e9b8).

If you want to...

- apply a patch, `bumpversion patch`
- update version with no breaking changes (minor version update), `bumpversion minor`
- update version with breaking changes (major version update), `bumpversion major`
- create a release (tagged in vesrion control - Git), `bumpversion --tag release`

<p><small>Project based on the <a target="_blank" href="https://github.com/knu2xs/cookiecutter-geoai">cookiecutter GeoAI project template</a>. This template, in turn, is simply an extension and light modification of the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
