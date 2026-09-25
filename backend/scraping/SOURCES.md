# Event sources

Research on structured event data (ICS, feeds, JSON APIs, schema.org,
tables) for events in the city of Münster. All numbers are upcoming events
as fetched on 2026-09-25 and will drift.

Each candidate was found by a search agent and then re-fetched by an
independent verifier, which parsed ICS feeds the same way as
`ICalendarSpider`, checked robots.txt, terms and Münster scope, and
estimated the integration effort.

## Spiders

### Base classes

- **`ICalendarSpider`** (`spiders/ics/`) reads an ICS feed (`ics_url`).
  All-day events and events without `DTEND` get the defaults of RFC 5545
  (all-day events have no times, the exclusive end date is adjusted).
  Events with an invalid start or end, or without `UID` or `SUMMARY`, are
  skipped with a warning instead of ending the crawl. `default_location`
  is used for events without (or with an empty) `LOCATION`.
  `convert_utc_times = True` converts start and end times with a time zone
  to Europe/Berlin, for feeds with real UTC times (`…Z`). It is off by
  default, see the time zone limitation below. `placeholder_duration`
  leaves out ends that a feed made up, e.g. pretix and
  evangelische-termine.de set DTEND = DTSTART + 1 h for events without an
  end (real one-hour events lose their end, too).
- **`TribeEventsSpider`** (`spiders/tribe/`) reads the REST API of the
  WordPress plugin The Events Calendar (`base_url`). Its ICS export is
  capped at 30 events, the API is paginated. `source_event_id` has the
  format of the ICS export's UIDs, so spiders switched from ICS keep most
  IDs. The export uses other IDs for some single events (e.g. all of
  Friedenskapelle's), those events already imported from ICS are imported
  once more (in the local test DB: 2 of Hafenkäserei, 1 of StattReisen).
  The API returns events of the next `days_ahead` (365) days.
  `default_location` is used for events without a venue, `ignore_venue`
  for sites misusing the venue field. Venue coordinates are passed on.
- All spiders send the user agent `muenster-update (+https://muenster-update.de/)`
  (`EventSpider.custom_settings`), `yesticket.org` blocks Scrapy's default
  one.
- **Geocoding** (`DatabaseExportPipeline`): Locations get the coordinates
  from the source if it has them (Stadt Münster calendar, Tribe venues),
  also existing locations without coordinates. Otherwise Nominatim is
  asked at most once per second and failed requests are not retried
  (`URLLibAdapter`, `RateLimiter(max_retries=0)`); a location whose
  geocoding fails is saved without coordinates, so it is not requested
  again in the next crawl. After an error of the service (e.g. rate
  limited, blocked, timeout) Nominatim is not asked again in the same
  crawl. Events without a location are dropped before geocoding.
- **`visible`**: `stadt_muenster_kalender`, `ekvw_ms` and `hotjazzclub` set
  it for every event (hidden if cancelled or moved). To keep a manual
  choice in the admin, add `visible` to the event's dirty fields.
- `SanitizeHTMLPipeline` removes `<script>` and `<style>` elements with
  their content from descriptions (KSHG embeds a calendar widget's JSON).

### Sources

Upcoming events per crawl on 2026-09-25:

| Spider | Source | Format | Upcoming | Notes |
| --- | --- | --- | --- | --- |
| `stadt_muenster_kalender` | Stadt Münster Veranstaltungskalender | GraphQL | ~1,600 | Public API of the calendar's web app (`events-calendar.stadt-muenster.de/graphql`, queries in `build/app/app.js`), replaces the HTML form scraping (the form now redirects to the web app). Dates starting in the next 30 days or still running, since it is crawled hourly and recurring events are listed for years. Cancelled or moved dates are hidden. Skips dates of organizers/venues with their own spider (Rieselfelder, Friedenskapelle, Hot Jazz Club, Peng!, Skaters Palace, StattReisen; Kulturbahnhof Hiltrup only as venue, its exhibitions are not in its ticket shop). Skaters Palace concerts thus lose the start time the Stadt calendar has. Also contains the k3 tours. |
| `ekvw_ms` | Evangelische Kirche von Westfalen (congregations in Münster) | ICS | ~1,310 | Location from the address in the description. Skips test entries, hides "fällt aus". Placeholder ends (+1 h) are left out. `source_event_id` without the start time from the UID, so moved events keep it. |
| `coerde_events` | Coerde Events (open data, CC BY 4.0) | ICS | ~310 | Skips events taken from the Stadt Münster calendar. |
| `kshg` | KSHG Münster | Tribe REST | ~280 | Mostly weekly services. |
| `hotjazzclub` | Hot Jazz Club | Tribe REST | ~145 | No venues, fixed location; hides "Konzertabsage", "Konzertverschiebung", "abgesagt", "verschoben auf". |
| `friedenskapelle` | Friedenskapelle Münster | Tribe REST | ~110 | Was ICS. |
| `cactus_theater` | Cactus Junges Theater | Tribe REST | ~75 | Was ICS. |
| `hafenkaeserei` | Genusshafen Münster GmbH | Tribe REST | ~65 | Was ICS (30 events). |
| `skaters_palace` | Skaters Palace | Tribe REST | ~55 | All-day events without times; the venue field holds tour names, fixed location. |
| `wolbeck` | Münster-Wolbeck in Südost (district portal) | Tribe REST | ~55 | |
| `rare_guitar` | Rare Guitar | Tribe REST | ~50 | Was ICS (30 events). |
| `stattreisen` | StattReisen Münster (city tours) | Tribe REST | ~47 | Was ICS. |
| `kulturbahnhof_hiltrup` | Kulturbahnhof Hiltrup e.V. | ICS (pretix) | ~28 | Skips the gift voucher entry. Placeholder ends (+1 h) are left out, URL is the ticket shop page from the description. |
| `st_liudger_ms` | Pfarrei St. Liudger Münster | ICS | ~17 | |
| `peng_impro` | Peng! Improvisationstheater | ICS (yesticket) | ~16 | |
| `hawerkamp` | Hawerkamp 31 e.V. | ICS | ~13 | Each exhibition day is an event. |
| `repaircafe_ms` | Repair Café Münster | ICS | ~11 | Redirects unknown user agents to google.com. |
| `fusion_club`, `fade_club`, `heaven` | Fusion Club, Fade Club, heaven | ICS | ~9, ~9, ~7 | No `LOCATION`, fixed address (without the club name, which Nominatim does not know). |
| `rieselfelder` | Biologische Station Rieselfelder Münster | ICS | ~8 | |
| `impro005` | IMPRO 005 | ICS | ~8 | |
| `seniorenvertretung_ms` | Kommunale Seniorenvertretung Münster | ICS | ~5 | |
| `studierendenwerk_ms` | Studierendenwerk Münster | Tribe REST | ~75 | Was ICS, which only had the current month. Rate limits quickly (429). |
| `bennohaus` | Bennohaus | ICS | ~4 | |
| `f24_kultur` | F24 Kulturkneipe | ICS (Events Made Easy) | ~2 | Real UTC times, `convert_utc_times`. Skips Peng! shows (in `peng_impro`). `source_event_id` without the times from the UID. |
| `alzheimer_ms` | Alzheimer Gesellschaft Münster e.V. | ICS | ~3 | |
| `k3` | k3 stadtführungen | XML | 0 | **Broken**: the open data XML returns 404. The tours are in the Stadt Münster calendar; k3's ticket shop also has a Tribe REST API. |
| `muensterland`, `muensterland_ev` | münsterLAND.digital, Münsterland e.V. | JSON | | Not re-checked (need credentials). |

### Remaining limitations

- **Time zones in `ICalendarSpider`.** By default the wall-clock time of
  `DTSTART` and `DTEND` is stored without conversion. That is right for
  `TZID=Europe/Berlin` and also for The Events Calendar sites whose
  WordPress time zone is set to UTC (they label local times as `TZID=UTC`,
  e.g. Hawerkamp, IMPRO 005), which a conversion would shift by 1–2 hours.
  Feeds with real UTC times (`…Z`) are 1–2 hours off without it, so they
  need `convert_utc_times = True`, like `f24_kultur` (Events Made Easy).
  Indico and Drupal feeds need it too when they are added.
- **`ORGANIZER`** of ICS feeds is stored as `MAILTO:…`.
- **Nominatim** finds addresses, but often not venue names that are unknown
  to OpenStreetMap ("Hot Jazz Club, Hafenweg 26b, …" fails,
  "Hafenweg 26b, 48155 Münster" works).
- **Duplicates across sources** remain where no rule exists yet (e.g.
  Stadt Münster calendar and Bennohaus or the Protestant congregations).
- **`source_event_id` of Tribe events contains start and end**, like the
  ICS UIDs of many feeds (e.g. `coerde_events`): when a site changes an
  event's time, it is imported as a new event and the old one stays.
- **Recurring ICS events** (`RRULE`) are not expanded; none of the current
  feeds has them.

## Candidates

### Priority 1

| Source | Endpoint | Format | Upcoming | Work needed |
| --- | --- | --- | --- | --- |
| B-Side | `https://cms.b-side.ms/api/events?where[eventDate][greater_than_equal]=…` | Payload CMS JSON | 100 | Simple JSON spider; location is free text but always Am Mittelhafen 42. |
| Sputnikhalle / Sputnik Café | `https://sputnikhalle.de/wp-json/wp/v2/posts?categories=22` | WP REST | 69 | Post date is the event day; the time ("Beginn"/"Einlass") has to be parsed from the content. |
| cuba (Cuba Nova, Black Box) | `https://cuba-muenster.de/wp-json/wp/v2/event?per_page=100` | WP REST | 40 | Date in `meta.event_date_start`, venue taxonomy `event_venue`. |
| Theater im Pumpenhaus | `https://pumpenhaus.de/wp-json/stec/v2/get/events/<from>/<to>` | Stachethemes JSON | 40 | Titles contain HTML. |
| Gleis 22 | `https://gleis22.de/programm/` | schema.org microdata | 34 | List has date only; times in "Beginn: 20:00" text or on detail pages. |
| stagedates (ticketing, nightlife) | `https://stagedates.com/events/api/events?size=3000` | JSON (public, no auth) | 38 in Münster | One request for the whole platform; filter on normalized city (`Münster`/`Muenster`, not "Münster (Hessen)"). Venues with address and geo: W² Weinerei, Club Favela, heaven, Fusion, Freundschaft, Dockland, … (overlaps with `heaven` and `fusion_club`). UTC times. |
| Brauns Märkte (flea markets) | `https://braunsmaerkte.de/` (JSON in page props) | JSON | 37 in Münster | Preußenstadion every Wed/Sat, plus Media Markt, Hornbach, Stadthalle Hiltrup. Filter on zip 4814x–4816x; UTC → Europe/Berlin is required (dates shift); times only as text ("6 Uhr - 14 Uhr"). |

### Priority 2

| Source | Endpoint | Format | Upcoming | Work needed |
| --- | --- | --- | --- | --- |
| LWL cultural institutions | `https://www.lwl.org/nozope/offline/lwlkalender-gesamt.xml` | XML (open data) | 569 (321 in Münster) | Filter `ort == "Münster"` (Planetarium, Naturkunde, Kunstmuseum). |
| Universität Münster calendar | `https://www.uni-muenster.de/de/veranstaltungskalender/prod/ausgabe/termine.php?layout=toptermin-ergebnis&…` | hCalendar HTML | 534 | The central ICS is stale (last event 2023). |
| yuki family magazine | `https://yuki-magazin.de/wp-json/wp/v2/veranstaltungen?_fields=id,title,link,acf` | WP REST | ~1,270 dates | Münster and Münsterland mixed; one post per date. |
| MCC Halle Münsterland | `https://www.mcc-halle-muensterland.de/de/gaeste/veranstaltungen` | HTML list + JSON-LD | 167 | JSON-LD has date only; times in HTML. |
| Indico Universität Münster | `https://indico.uni-muenster.de/category/0/events.ics` | ICS | 148 | Real UTC times; includes internal items and placeholder dates (9999-09-09). Crawl-delay 10. |
| Kreativ-Haus | per-event `…/veranstaltung/<slug>.ics` | ICS per event | 99 | No list feed: 1 + ~100 requests. |
| na dann (weekly magazine) | `https://www.nadann.de/veranstaltungen` → day pages | JSON-LD | 89 | Dates in Java `toString` format. |
| Akademie Franz Hitze Haus | `https://www.franz-hitze-haus.de/feed.rss` | RSS | 71 | `pubDate` is the event start (labelled GMT, really local time). |
| Stadt Münster council meetings | `https://www.stadt-muenster.de/sessionnet/sessionnetbi/termine.php` | ICS (SessionNet) | 70 | Works as is, but titles are just the body ("Rat", "Ausschuss für …"), no URL. OParl alternative: `https://oparl.stadt-muenster.de/bodies/0001/meetings`. |
| münster gründet! | `https://www.muenster-gruendet.de/wp-json/tribe/events/v1/events` | Tribe REST | 61 | A third are online webinars. |
| Sternfreunde Münster | `https://sternfreunde-muenster.de/sternfreunde.ics` | ICS | 50 | UIDs contain the export time and change with every export (would create duplicates); some `DTSTART` values are malformed. |
| Baracke | `https://export.calendar.online/ics/1082832/baracke/konzerte.ics?…` (and other public sub-calendars) | ICS | ~48 | Many all-day entries; the full calendar mixes in internal sub-calendars. |
| Theater Münster | `https://www.theater-muenster.com/spielplan?date=YYYY-MM` | HTML | ~40-60 per month | No structured data; stable HTML blocks. |
| Pension Schmidt | `https://www.pensionschmidt.se/programm` | HTML + JSON-LD | 39 | `?format=json` works but robots.txt forbids it. |
| Mühlenhof-Freilichtmuseum | `https://www.muehlenhof-muenster.org/veranstaltungskalender/` | Inline FullCalendar JSON | 36 | Parse the embedded data script. |
| Kunstmuseum Pablo Picasso | `https://api.koronaevent.de/graphql` | GraphQL (ticket shop) | 33 | Venue must be set; times as UTC ranges. |
| SC Preußen Münster | `https://api.openligadb.de/getmatchesbyteamid/188/0/40` | JSON (OpenLigaDB) | 31 (16 home) | Keep home games only; kickoff times are placeholders until scheduled. |
| Kulturserver NRW | `https://kulturserver-nrw.de/de_DE/event.json?city_region_location=city_2221` | JSON | 23 | Paginated (20 per page). |
| USC Münster volleyball | `https://www.volleyball-bundesliga.de/iCal/team/matches.ical?teamId=781343629&calenderType=ics` | ICS | 22 (11 home) | 100 % compatible, but filter away games. |
| Heimatfreunde Angelmodde | `https://heimatfreunde-angelmodde.de/?post_type=tribe_events&ical=1&eventDisplay=list` | ICS | 22 | No `LOCATION` → `default_location`; drop "Privater Termin". |
| Kulturquartier Münster | `https://www.kulturquartier-muenster.de/veranstaltungen/` | JSON-LD (EventON) | 20 | Deduplicate; fixed venue. |
| ADFC Münster | `https://api-touren-termine.adfc.de/api/eventItems/search?lat=51.96&lng=7.63&distance=10&…` | JSON | 17 | Some internal board meetings. |
| Club Favela | `https://clubfavela.de/sitemap.xml` → JSON-LD per event | JSON-LD | 16 | robots.txt disallows the Payload `/api/`. |
| evis.events (REACH start-up centre) | `https://evis.events/export/categ/27.ics?from=today` | ICS (Indico) | 14 | Filter template events ("Klonvorlage"); real UTC times. |
| Meetup groups (e.g. Code for Münster) | `https://www.meetup.com/<group>/events/ical/` | ICS | ~9 per group | No `LOCATION`, some groups online only; curate groups. Served without charset (check UTF-8 decoding). |
| Münster Alternativ | `https://ms-alternativ.de/rss.xml` | RSS | 8 | Filter non-event items; real UTC. |
| Westfälischer Kunstverein | `https://westfaelischer-kunstverein.de/api/event-list?seq=1000&category=all` | JSON | 8 | No end date or location. |
| Hospizbewegung Münster | `https://hospizbewegung-muenster.de/?post_type=tribe_events&ical=1&eventDisplay=list` | ICS | 23 | 2 events without location, some marked "interne Veranstaltung". |
| meine-kunsthandwerker-termine.de | `https://meine-kunsthandwerker-termine.de/ort/muenster?page=N` | JSON-LD | 100 (one per market day) | The Christmas markets (Aegidiimarkt, Rathaus, Lambertikirche, Mühlenhof), missing from all current sources. Dates only in JSON-LD, times on detail pages; double entity-encoded text. Commercial directory (database right, take only the Münster subset). |
| meine-flohmarkt-termine.de | `https://meine-flohmarkt-termine.de/ort/muenster?page=N` | JSON-LD | 47 | Same operator and markup as above. Filter postal code 481xx (one "Münster" in Hessen). |
| Krebsberatung im Münsterland | `https://krebsberatung-muenster.de/wp-json/tribe/events/v1/events` | Tribe REST / ICS | 38 | ICS 100 % compatible, no `LOCATION` (mostly Gasselstiege 13 → `default_location`); about half are individual consultation slots. |
| love your artist (ticketing) | `https://prod.loveyourartist.com/api/v1/store/events?filter[venue.city][$eq]=Münster&filter[endAt][$gte]=<epoch ms>` | JSON | 27 | Mostly Pension Schmidt and Sputnik; honour `canceled`. |
| vivenu ticket shops | e.g. `https://puls-qk2z.vivenushop.com/`, `https://freischnauzeshow-m3y0.vivenushop.com/` | JSON in `__NEXT_DATA__` | 3 (PULS), 10 in Münster (Comedy Werkstatt) | One generic spider per seller list; filter `locationCity == "Münster"`. `/api/` is disallowed, the seller page is allowed. |
| YesTicket organisers (impro groups) | `https://www.yesticket.org/ical/<organizer>.ics` (`querfaelltein`, `rosa-pfeffer`, `scharf-im-wolfspelz`, `tpz`, `cir`) | ICS | ~1 each | 100 % compatible (like `peng_impro`). The paginated city listing is disallowed by robots.txt. |
| Gesundheitshaus Münster (city) | `https://www.gesundheitshaus-muenster.de/de/programm/das-aktuelle-programm/` | HTML | 95 series | Two-level HTML spider; skip self-help groups and rehab sport, keep cooking courses and talks. |
| Eine Welt Forum | `https://eineweltforum-muenster.de/events/?ical=1` | ICS | 2 | No location; title prefix "MÜNSTER, DD.MM.YYYY: ". |

### Priority 3

Low volume or marginal: Jugendzentrum Paul-Gerhardt-Haus
(`pg-muenster.de/veranstaltungen/?ical=1`, 30), Bürgernetz Münster
(`buergernetz-muenster.de/events.ics`, one weekly consultation hour),
Café Seniorentreff Hansahof (`…/feed/my-calendar-ics/?span=year`),
Heimatverein Wolbeck, Greenpeace Münster, Veranstaltungskalender Münster Ost,
Yolk (Tribe REST, mostly "geöffnet"/"Ruhetag" entries), Stadtsportbund
(`ssb.ms/veranstaltungen/`, JSON-LD, 7), Critical Mass
(`criticalmass.in/api/ride?citySlug=muenster`, monthly), AStA (JEvents RSS),
Haus Rüschhaus (per-event ICS on `burg-huelshoff.de`, most events are
outside Münster), Vamos e.V. (Tribe REST), UKM and St. Franziskus-Hospital
(TYPO3 event lists, 14 and 12), Rudelsingen (vivenu, 2 per year at Jovel),
basarlino.de (children's bazaars, 6), flowl.de (Tribe REST, 6 Münster flea
markets among 282).

## Not recommended

- **Terms forbid automated extraction or bot protection:** Eventbrite,
  Rausgegangen, allevents.in, Songkick, Livegigs, ADticket/Reservix,
  regioactive, eventfinder, Resident Advisor, Bandsintown, Eventim.
  SPD Münster (ICS only reachable with a spoofed browser user agent,
  CloudFront WAF).
- **robots.txt disallows the feed:** public Google Calendar ICS URLs
  (`calendar.google.com/robots.txt` disallows everything), e.g. warpzone,
  NABU Münster, Uni Baskets, Lindy Hop, Fahrradstadt.ms. These are the
  official subscription links, and `crawl` does not obey robots.txt, so
  using them is a policy decision. Same for ChurchTools calendars
  (Christengemeinde, Emmanuel House, Baptisten).
- **Needs registration or API key:** DZT Open Data Knowledge Graph,
  Tourismus NRW Data Hub, Ticketmaster Discovery API, foodsharing, LADV,
  Floorball Saisonmanager.
- **Out of scope or low value:** ibb.info (Ibbenbüren), DRK blood donation
  dates, TaijiDao courses (~520 weekly class dates), Grüne Münster (mostly
  internal meetings), FH Münster GraphQL (no venue data), Luma (3 events),
  instaff.jobs trade fair list, AVR Messe (2 trade fairs), HofFloh (2 yard
  sales), unser-ferienprogramm.de (holiday childcare), DMSG (RRULE series
  only), Bundesagentur für Arbeit event database (needs an undocumented API
  key header, job events), Gemeinschaftswerk Nachhaltigkeit (7, fuzzy
  location match), Woche der Seelischen Gesundheit (1 Münster row).
- **Medizinische Fakultät** Atom feed
  (`medizin.uni-muenster.de/fileadmin/atomfeed/atomfeeddates.xml`, 44):
  disallowed by robots.txt.

## Checked without usable structured data

HTML only or nothing found: Wolfgang Borchert Theater, Der Kleine
Bühnenboden, Boulevard Münster, GOP Varieté, Jovel, Triptychon (empty
Tribe feed), Cinema & Kurbelkiste, Schloßtheater/Cineplex (403),
Allwetterzoo, Kunsthalle Münster, Kunstakademie, LWL museum websites
(use the LWL XML), VHS Münster (JSON-LD per course page only), Stadtbücherei
and other city institutions (already in the city calendar), Bistum Münster
(diocese-wide), CDU, FDP, Die Linke, Volt, fussball.de (no iCal export),
Hochschulsport (SSO). Platforms without Münster events:
radar.squat.net, Mobilizon, Gancio, OSMCAL. The open data portal
`opendata.stadt-muenster.de` has no event datasets besides the Münsterland
datenportal and Digital Hub sources already used.
