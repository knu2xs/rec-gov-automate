# rec-gov-automate

Automate tasks when interacting with Recreation.gov

## Getting Started

1 - Clone this repo.

2 - Create an environment with the requirements.

**TODO:** Add browser installation to `make env`
    
```
make env
```

## References

### Middle Fork (Permit ID: 234623)

#### Access Codes

* 2012 - Thomas Creek Airstrip
* 2100 - Boundary Creek Launch (Normal Putin)
* 2101 - Indian Creek Launch & Airstrip (Low Water Fly-In)
* 2103 - Mahoney Airstrip
* 2104 - Loon Creek tributary
* 2105 - Flying Resort Ranch (private)
* 2106 - Bernard Airstrip
* 2200 - Marsh Creek tributary
* 2201 - Pistol Creek Ranch (private)
* 2203 - Lower Loon Airstrip
* 2204 - Camas Creek tributary
* 2205 - Big Creek tributary

#### Permit Pickup Codes

* 2300 - Boundary Creek
* 2301 - Indian Creek Guard Station
* 2302 - SCNF River Office

### Main Salmon (Permit ID: 234622)

#### Access Codes

* 2400 - Corn Creek (Normal Putin)
* 2401 - Allison Ranch
* 2402 - Yellow Pine Bar
* 2403 - Whitewater Ranch
* 2404 - Campbell's Ferry
* 2405 - Wilson Bar
* 2406 - Mackay Bar
* 2407 - Shepp Ranch
* 2408 - Vinegar Creek Boat Ramp (Jet Boat Launch Access)
* 2409 - Carey Creek Boat Ramp (Normal Takeout)
* 2410 - Spring Bar Boat Ramp

#### Permit Pickup Codes

* 2412 - Corn Creek Guard Station
* 2411 - SCNF River Office

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
