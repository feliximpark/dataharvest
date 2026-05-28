---
title: "Exploring Extreme Heat: Satellite imagery and spatial analysis in R"
author: "Max Donheiser"
format: html
editor: visual
---

Which neighborhoods in Brussels are most affected by extreme heat? Which areas tend to stay cool? And how many people are affected?

In this tutorial, you will use code and satellite imagery to analyse urban heat islands in the European capital city of Brussels. We will be working with images from [Landsat Level-2 Collection-2](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products), which provide data on surface temperature with a spatial resolution of 30m. All images were taken on summer days (minimum air temperature of 25C).

You will also use publicly available data from Datastore (the open data platform for the city of Brussels) and Statbel (the Belgian statistical office) to further contextualize your results.

The purpose of this guide is to provide a boilerplate analysis that can be adjusted for similar investigations elsewhere.

If you want to explore heat analysis for a larger geographic area, you can also download imagery from [Copernicus Sentinel-3 SLSTR](https://sentiwiki.copernicus.eu/web/s3-slstr-instrument) to work with. The images have a spatial resolution of 1km.

## Setting up

First step is loading the necessary R packages for data processing and analysis.

```{r}
library(dplyr) # data manipulation
library(terra) # geodata
library(tidyterra) # more data manipulation
library(ggplot2) # data visualization
```

Now, you can load one of the images and take a look.

```{r}
landsat <- rast('landsat-l2c2-brussels-2025/LC09_L2SP_199025_20250813_20250815_02_T1_ST_B10.TIF')

plot(landsat)
```

Cool! But where's Brussels? In order to find the city in the image, a good first step is loading the its borders. They can be downloaded from the [Datastore](https://datastore.brussels/web/data/dataset/f6b83500-6a62-11ed-be6d-010101010000#access), the open data portal for Brussels. The file also contains boundaries for different neighborhoods, which will be useful for later in the analysis.

Note: The data can also be accessed via a Web Feature Service (WFS), which provides a interface for requesting for geographical features. It's basically an API for geodata.

Back to the file. Since this is a GeoPackage, it has multiple layers. You can look at the different layers with the following command:

```{r}
vector_layers("data/UrbISAdminUnits_04000.gpkg")
```

The monitoring districts are the different neighborhoods in Brussels. That's a good place to start.

```{r}
brussels <- vect("data/UrbISAdminUnits_04000.gpkg", layer="MonitoringDistricts")

plot(brussels)
```

If you want to inspect the file further, you can can preview the data with the `head` command.

```{r}
brussels |>
  head()
```

The file contains an ID, the monitoring district name in French and Dutch, as well as some other information. If you needed to filter the data to a specific district, you could use the classic `terra` function:

```{r}
#| echo: true
district <- subset(brussels, brussels$NAMEDUT=="LOUIZA - LANGEHAAG")

plot(district)
```

Or more of a `dplyr` style filter:

```{r}
#| echo: true

district <- brussels |>
  filter(NAMEDUT=="LOUIZA - LANGEHAAG")

plot(district)
```

## Projections, cropping and masking

Now it's time to find Brussels on the map. The first step is checking that the raster image and the city boundaries are in the same projection. Otherwise, the calculations won't work. The projects can be checked quite easily.

```{r}
#| echo: true
crs(landsat, describe=TRUE)

crs(brussels, describe=TRUE)
```

You can also quickly check whether two geographic datasets have the same coordinate reference system with the `same.crs` command.

```{r}
#| echo: true
same.crs(landsat, brussels)
```

Since the projections are different, one of the objects has to be reprojected. The district boundaries for Brussels are a bit smaller, so that will be faster to reproject.

```{r}
new_crs <- crs(landsat)

brussels <- brussels |>
  project(new_crs)

plot(brussels)
```

Notice that the plot looks the same, but the axes have different values. Now you can plot the Brussels districts on top of the satellite image.

```{r}
plot(landsat)
plot(brussels, add=TRUE)
```

And finally, you can crop the image to just the area of interest. Note: Cropping only adjusts the *extent* of an image. That is, the maximum bounds or x and y values.

```{r}
#| echo: true
landsat <- crop(landsat, brussels)
plot(landsat)
plot(brussels, add=TRUE)
```

You further reduce the image to just the area within Brussels by applying a *mask*.

```{r}
landsat <- mask(landsat, brussels)
plot(landsat)
plot(brussels, add=TRUE)
```

Now you only have data for within the geographic boundaries of Brussels. This will make your calculations later run much faster. And if you want to combine both steps, you could run the function `crop(landsat, brussels, mask=TRUE)`.

## Raster bands and calculations

You may have noticed that the plot legend is not in Celsius. The metric being shown is actually is a digital number, or DN for short. The actual definition and calculation of that is a bit complicated, but luckily you don't need to get so into the details. Landsat provides a simple [scaling formula](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products) for converting DN into Kelvins: K = (DN \* 0.00341802) + 149.0. From there, converting to Celsius is easy.

So how do you do this in code? Calculations with raster data are pretty similar to working with normal dataframes in R, except instead of having columns the data has bands. Landsat GeoTIFF files only contain one band per file. Try taking a look at the different band names:

```{r}
varnames(landsat)
```

Now you can apply the scaling formula and save it to a new band called `lst_kelvin`.

```{r}
landsat$lst_kelvin <-  (landsat$LC09_L2SP_199025_20250813_20250815_02_T1_ST_B10 * 0.00341802) + 149.0

plot(landsat$lst_kelvin)
```

And now, you can convert from Kelvin to Celsius.

```{r}
landsat$lst_celsius <- landsat$lst_kelvin - 273.15
plot(landsat$lst_celsius)
```

## Zonal statistics

This is where things get interesting. How can you find out which neighborhoods are most affected by heat? Since the data is a raster image, you can calculate the average values of all pixels that fall within a given neighborhood boundary. These types of calculations are called zonal statistics, in our case each neighborhood (or monitoring district) is a zone.

You can do that super easily using the `extract` function.

```{r}
#| echo: true
extract(landsat$lst_celsius, brussels, fun=mean, )
```

The results show the average temperature for each neighborhood. The ID here is the row number of each district. Save the results as a new column, and plot them.

```{r}
#| echo: true
brussels$mean_lst <- extract(landsat$lst_celsius, brussels, fun=mean, ID=FALSE)

plot(brussels, "mean_lst")
```

That was easy! You can already see that the center of Brussels tends to be a bit hotter than the other areas. With a few small tweaks, you can make the plot even better.

```{r}
#| echo: true
plot(brussels, "mean_lst", type="continuous", col=hcl.colors("Reds", n=100, rev=TRUE))
```

## Spatial resolution and weighted means

Spatial resolution is an important component when working with raster data. The Landsat data has a resolution of 30m, which isn’t terrible, but also not super detailed. There are likely many pixels that fall on the border between two neighborhoods. You can investigate that a bit further by looking again at the neighborhood LOUIZA - LANGEHAAG.

```{r}
#| echo: true

district <- brussels |>
  filter(NAMEDUT=="LOUIZA - LANGEHAAG")

landsat_district <- crop(landsat, district, mask=TRUE)
plot(landsat_district, "lst_celsius")

plot(district, add=TRUE, border="white")
```

As you can see, the many pixels don't fit neatly into just one neighborhood. By default, the `extract` function assigns pixels to the geometry in which their geographic midpoint fall. When working with very high-resolution raster data or large geographic regions, this doesn't pose a huge issue.

However, the smaller your regions get or the lower your resolution is, this assignment method can have large impacts on your results: If a region overlaps with 500 raster data points, then losing a few does not make a huge difference. But if it overlaps just 10 raster cells, losing just one can have a lot of weight.

An alternative method for calculating zonal raster statistics is working with the weighted mean. This takes into account the approximate portion of a pixel that falls within a geometry while calculating summary statistics.

```{r}
#| echo: true
brussels$mean_lst_weighted <- extract(landsat$lst_celsius, brussels, fun=mean, weights=TRUE, ID=FALSE)

plot(brussels, "mean_lst_weighted", type="continuous", col=hcl.colors("Reds", n=100, rev=TRUE))
```

On first glance, this doesn't look so different that the original map. You can get a better sense of the effect by looking at a histogram of the difference in mean LST between the two methods.

```{r}
#| echo: true
brussels$weighted_diff <- brussels$mean_lst - brussels$mean_lst_weighted

brussels |>
  as.data.frame() |>
  ggplot(aes(weighted_diff)) +
  geom_histogram()
```

And if you look at the difference by district size, you'll notice that smaller districts were more impacted by the weighted mean than larger districts.

```{r}
#| echo: true
brussels$area_km <- expanse(brussels, unit="km")

brussels |>
  ggplot(aes(area_km, weighted_diff)) +
  geom_point()
```

For the final calculations, try working with the weighted mean.

## Global statistics

When analysing heat islands, the absolute surface temperature (i.e. neighborhood X was 35C) is not necessary the end goal. Rather, the focus is on the *relative* temperature, or where it gets hotter or cooler. This is also pretty easy to calculate: You just need to look at the deviation from the mean.

You can find the mean temperature of all of brussels with the `global` function.

```{r}
#| echo: true
global(landsat, fun=mean, na.rm=TRUE) 

# without na.rm=TRUE, we'll get an error, since the pixels that have been masked out have a value of NA
```

In order to calculate relative mean temperature, just subtract the global mean from the neighborhood means.

```{r}
#| echo: true
global_mean_lst <- global(landsat$lst_celsius, fun=mean, na.rm=TRUE)$mean

brussels$rel_lst <- brussels$mean_lst_weighted - global_mean_lst

plot(brussels, "rel_lst", type="continuous", col=hcl.colors("RdYlBu", n=100, rev=TRUE))
```

Amazing! Now you can easily see which neighborhoods in Brussels were hotter than others at the time the satellite image was taken. Let's take a closer look at the data.

```{r}
#| echo: true
brussels |>
  as.data.frame() |>
  slice_max(rel_lst, n=3) |>
  select(NAMEDUT, mean_lst_weighted, rel_lst)
```

The HERTOGIN neighborhood was the hottest: An average 6 degrees Celsius warmer than Brussels as a whole!

But before drawing any major conclusions, you should take into account a larger sample size...

## Building a data pipeline

To streamline things, you can write a function in R to repeat this analysis for multiple images. For more information on writing functions in R, see this chapter from Hadley Wickham's excellent [R for Data Science](https://r4ds.had.co.nz/index.html))

```{r}
#| echo: true
get_relative_lst = function(fpath, vector) {

  # load files
  raster <- rast(fpath)

  # reproject if necessary
  if (!same.crs(raster, vector)) {
    new_crs = crs(raster)
    vector = project(vector, new_crs)
  }

  # crop and mask
  raster <- crop(raster, vector, mask=TRUE)

  # convert from DN to celsius (or whatever other calculation you might need to do)
  raster <- (raster * 0.00341802) + 149.0 - 273.15

  # calculate zonal statistics
  mean_lst <- extract(raster, vector, fun=mean, ID=FALSE)

  # calculate global statistics
  global_mean <- global(raster, fun=mean, na.rm=TRUE)$mean

  # calculate relative values
  relative_lst <- mean_lst - global_mean

  # and return
  return(relative_lst)
}
```

Now you can all the images by looking for files with the .TIF extension in a directory.

```{r}
#| echo: true
# generate list of all images

landsat_list <- list.files("landsat-l2c2-brussels-2025/", pattern=".TIF", full.names = TRUE)

landsat_list
```

And then, apply the function to the file list.

```{r}
#| echo: true
rel_lst_list <- lapply(landsat_list, get_relative_lst, vector=brussels)
```

The result is a list of dataframes. You can convert them into one file with the following command:

```{r}
#| echo: true
rel_lst_df <- do.call(cbind, rel_lst_list)

rel_lst_df |>
  head()
```

You’ll notice that each column is the name of the file it came from. Now you just need to calculate the mean relative LST across each of the images and save this as a new column.

```{r}
#| echo: true
brussels$mean_rel_lst <- rowMeans(rel_lst_df)

plot(brussels, "mean_rel_lst", type="continuous", col=hcl.colors("RdYlBu", n=100, rev=TRUE))
```

## Adding population data

The story doesn't stop there. Now it's time to look for additional data to help contextualize your results. How many people are affected? Is there a correlation between income and heat? And many other possible questions. Below is some example code focused on population data to get you started. The data sources is population from [Statbel](https://statbel.fgov.be/en/open-data/population-statistical-sector-12), the statistical office for Belgium.

```{r}
library(readxl)

pop <- read_excel("data/OPENDATA_SECTOREN_2025_NEW.xlsx")

pop |>
  head()
```

Filter to just Brussels and relevant columns.

```{r}
pop <- pop |>
  filter(TX_DESCR_NL == "Brussel") |>
  select(pop = TOTAL, district_dutch = TX_DESCR_SECTOR_NL)

pop |>
  head()
```

Merge and voila!

```{r}
brussels = brussels |>
  merge(pop, by.x="NAMEDUT", by.y="district_dutch")

brussels |>
  select(NAMEDUT, mean_rel_lst, pop) |>
  head()
```