[Meshtastic](https://meshtastic.org/docs/configuration/device-uis/meshtasticui/#map) and various [MeshCore firmwares](https://github.com/dabeani/meshcore/issues/49#issuecomment-3805994837) allow users to view maps using tiles from sources like OpenStreetMaps. There are [existing](https://github.com/tekk/map-tiles-downloader) [tools](https://github.com/JustDr00py/tdeck-maps) for downloading these map tiles, though it is unfriendly to the [OpenStreetMaps Project](https://osmfoundation.org/) to mass-scrape all tiles.

The below datasets are prepared tile sets that can be downloaded, unzipped and [copied to your device](https://www.jeffgeerling.com/blog/2025/adding-gps-and-grid-maps-my-meshtastic-t-deck/) without needing to bombard OSM for fresh tiles.

- **ColoradoMesh_OSM_20260408.zip** - OpenStreetMaps as of 2026-04-08, featuring worldwide tiles up to Zoom Level 4, United States tiles up to Zoom Level 9, and Colorado tiles up to Zoom Level 16.
  - **NOTE:** Some tiles around the borders of Colorado are unavailable after Zoom Level 10 due to the tool used to collect these tiles.  
