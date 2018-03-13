
# Releases

## Current version
* [Open issues](https://its.cern.ch/jira/browse/ACTS-203?filter=18687)
* [git repository](https://gitlab.cern.ch/acts/acts-core)
* [Documentation](http://acts.web.cern.ch/ACTS/latest/doc/index.html)

## History
| release | time | links |
| ------- | ---- | ----- |
{%- for tag in tags %}
| {{ tag.name }} | {{ tag.commit.authored_date|iso8601|datetime_format("%d %b %Y %H:%M") }} | [Release Notes](http://acts.web.cern.ch/ACTS/{{ tag.name }}/ReleaseNotes.html), [Download](http://acts.web.cern.ch/ACTS/{{ tag.name }}/ACTS-{{ tag.name }}.tar.gz), [Documentation](http://acts.web.cern.ch/ACTS/{{ tag.name }}/doc/index.html) |
{%- endfor %}