import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import folium
import gpxpy

class Route:

    HARD_SLOPE_THRESHOLD = 0.2 # Threshold to consider a section as hard (20% gradient)
    COLORS = {
        'main': '#f53b57',
        'secondary': '#3c40c6',
        'tertiary': '#ffdd59',
    }

    def __init__(self, gpx_file_path):
        self.gpx_file_path = gpx_file_path
        
        # Load and process the data
        self._load_gpx()
        self._process_data()
    
    def _load_gpx(self):
        """Load GPX file and extract track data.
        
        Extracts the points from the first track and segment of the GPX file and stores them
        as instance attributes.
        """
        # Read the GPX file
        self.gpx_file = gpxpy.parse(open(self.gpx_file_path))
        
        # Only extract the first track and segment
        self.track = self.gpx_file.tracks[0]
        self.segment = self.track.segments[0]
        self.points = self.segment.points
        
        # Extract coordinates into numpy array for later processing
        self.coordinates = np.array([
            [point.latitude, point.longitude, point.elevation] 
            for point in self.points
        ])

    def _process_data(self):
        """Process GPX data into a Pandas DataFrame with calculated metrics.
        
        Calculates:
        - Distances between points (cumulative and segment)
        - Elevations and elevation changes between points
        - Slopes between points
        - Moving averages for smoothing
        """
        
        # Create DataFrame
        self.df = (
            pd.DataFrame(
                self.coordinates,
                columns=['latitude', 'longitude', 'elevation']
            )
            .assign(
                # We add a 0 at the beginning to match the length of the DF
                elevation_diff=lambda x: np.concatenate(
                    [[0], np.diff(x['elevation'])]
                )
            )
        )
        
        # Calculate the cumulative distances and slopes
        self.distance_between_points_3d = np.zeros(len(self.points) - 1)
        self.distance_between_points_2d = np.zeros(len(self.points) - 1)

        for i in range(0, len(self.points) - 1):
            self.distance_between_points_3d[i] = gpxpy.geo.distance(
                self.df.iloc[i]['latitude'],
                self.df.iloc[i]['longitude'],
                self.df.iloc[i]['elevation'],
                self.df.iloc[i+1]['latitude'],
                self.df.iloc[i+1]['longitude'],
                self.df.iloc[i+1]['elevation']
            )

            self.distance_between_points_2d[i] = gpxpy.geo.distance(
                self.df.iloc[i]['latitude'],
                self.df.iloc[i]['longitude'],
                0, # Set elevation to 0 for 2D distance
                self.df.iloc[i+1]['latitude'],
                self.df.iloc[i+1]['longitude'],
                0, # Set elevation to 0 for 2D distance
            )

        # Bin the slopes - Define bin sizes and labels
        self.slope_bins = np.arange(-1, 1, 0.1).round(2)
        self.slope_bin_labels = [f"{round(100*self.slope_bins[i])} → {round(100*self.slope_bins[i+1])}%" for i in range(len(self.slope_bins) - 1)]

        self.df = (
            self.df
            .assign(
                distance_between_points_3d=np.concatenate(
                    [[0], self.distance_between_points_3d]
                ),
                distance_between_points_2d=np.concatenate(
                    [[0], self.distance_between_points_2d]
                ),
                # Calculate cumulative distance and convert to km
                cum_distance_3d_km=np.concatenate(
                    [[0], np.cumsum(self.distance_between_points_3d)/1000]
                ),
                cum_distance_2d_km=np.concatenate(
                    [[0], np.cumsum(self.distance_between_points_2d)/1000]
                ),
                # Calculate slope gradients
                slope_gradient=lambda x: x['elevation_diff']/x['distance_between_points_2d'],
                # Bin the slopes
                slope_bin=lambda x: pd.cut(
                    x['slope_gradient'] + 0.0001,
                    bins=self.slope_bins,
                    right=False,
                    labels=self.slope_bin_labels
                ),
                hard_slope=lambda x: abs(x['slope_gradient']) > self.HARD_SLOPE_THRESHOLD
            )
            .fillna(
                {
                    'slope_gradient': 0,
                    'slope_bin': '0 → 10%',
                }
            )
        )

    @property
    def total_distance(self):
        """Get total 3D distance in meters."""
        return self.segment.length_3d()

    @property
    def elevation_gain(self):
        """Get total elevation gain in meters."""
        return self.segment.get_uphill_downhill().uphill

    @property
    def elevation_loss(self):
        """Get total elevation loss in meters."""
        return self.segment.get_uphill_downhill().downhill
    
    @property
    def avg_elevation_gain_per_km(self):
        """The percentage of the total distance that is uphill."""
        return (self.elevation_gain / (self.total_distance / 1000))

    @property
    def center_coordinates(self):
        """Calculate the center point of the route."""
        return np.mean(
            self.df[['latitude', 'longitude']].values,
            axis=0
        )

    @property
    def bounds(self):
        """Get the geographical bounds of the route."""
        return {
            'min_lat': self.df['latitude'].min(),
            'max_lat': self.df['latitude'].max(),
            'min_lon': self.df['longitude'].min(),
            'max_lon': self.df['longitude'].max()
        }