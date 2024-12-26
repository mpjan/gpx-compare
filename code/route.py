import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import folium
import gpxpy

plt.ioff()  # Turn off interactive mode

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
        """The average elevation gain per km."""
        return (self.elevation_gain / (self.total_distance / 1000))
    
    @property
    def hard_slope_percentage(self):
        """The percentage of route with slopes above HARD_SLOPE_THRESHOLD.
        
        Returns:
            float: Percentage of route with hard slopes (0.0-1.0)
        """
        hard_slopes = abs(self.df['slope_gradient']) > self.HARD_SLOPE_THRESHOLD
        hard_slopes_percentage = hard_slopes.sum() / len(self.df)
        return hard_slopes_percentage

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
    
    def plot_map(self):
        """Create an interactive map of the route.
        
        Returns:
            folium.Map: Interactive map showing the route with start/end markers
        """
        # Create map with auto zoom based on center coordinates
        map = folium.Map(
            location=self.center_coordinates,
            zoom_start=12,
        )

        # Fit bounds to the route
        map.fit_bounds(
            [
                [self.bounds['min_lat'], self.bounds['min_lon']],  # Southwest corner
                [self.bounds['max_lat'], self.bounds['max_lon']]   # Northeast corner
            ]
        )

        # Add the route to the map
        folium.PolyLine(
            self.df[['latitude', 'longitude']].values,
            weight=5,
            color=self.COLORS['main'],
            opacity=0.8
        ).add_to(map)

        # Add the start point to the map
        folium.Marker(
            location=self.df.iloc[0][['latitude', 'longitude']].values,
            icon=folium.Icon(color='green', icon='circle'),
            popup='Start'
        ).add_to(map)

        # Add the end point to the map
        folium.Marker(
            location=self.df.iloc[-1][['latitude', 'longitude']].values,
            icon=folium.Icon(color='red', icon='circle'),
            popup='Finish'
        ).add_to(map)

        return map
    
    def plot_elevation_profile(self):
        """Create an interactive elevation profile plot.
        
        Returns:
            plotly.graph_objects.Figure: Interactive elevation profile plot
        """
        # Create the plot
        fig = px.line(
            x=self.df['cum_distance_3d_km'],
            y=self.df['elevation'],
            title='Elevation Profile',
            labels={
                'x': 'Distance (km)',
                'y': 'Elevation (m)'
            }
        )

        # Update line style and add fill
        fig.update_traces(
            line_color=self.COLORS['main'],
            line_width=2,
            fill='tonexty',
            fillcolor=f"rgba{tuple(int(self.COLORS['main'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}",
            mode='lines',
        )

        # Update layout
        fig.update_layout(
            showlegend=False,
            plot_bgcolor='white',
            width=900,
            height=400,
            hoverdistance=100,     # Maximum distance to show hover effect
            spikedistance=100,     # Maximum distance to show spike
            yaxis=dict(
                range=[self.df['elevation'].min() - 50, self.df['elevation'].max() + 50],
                tickformat='.0f',  # Format y-axis ticks to 1 decimal place
                showline=True,
                showgrid=True,
                gridcolor='lightgrey',
                showspikes=True,         # Show spike line
                spikecolor=self.COLORS['main'],
                spikesnap='data',      # Spike snaps to data points
                spikemode='across',      # Spike goes across the plot
                spikethickness=1
            ),
            xaxis=dict(
                tickformat='.1f',  # Format x-axis ticks to 2 decimal places
                showline=True,
                showgrid=True,
                gridcolor='lightgrey',
                spikemode='across',
                spikesnap='data',
                spikethickness=1,
                spikecolor=self.COLORS['main']
            ),
            yaxis_title='Elevation (m)',
            xaxis_title='Distance (km)',
        )

        return fig
    
    def plot_slope_histogram(self):
        """Create a histogram of the slope classifications.
        
        Returns:
            matplotlib.figure.Figure: Histogram showing distribution of slopes
        """
        # Calculate slope distribution
        slope_df = (
            self.df
            .groupby('slope_bin', observed=True)
            .size()
        )
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot the histogram
        slope_df.plot(
            kind='bar',
            color=self.COLORS['main'],
            ax=ax
        )
        
        # Customize the plot
        ax.set_title('Slope Distribution')
        ax.set_xlabel('Slope Grade (%)')
        ax.set_ylabel('Number of Points')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Add text showing percentage of hard slopes
        hard_slope_text = f"Slopes > {100*self.HARD_SLOPE_THRESHOLD:.0f}%: {100*self.hard_slope_percentage:.1f}%"
        plt.text(
            0.95, 0.95, 
            hard_slope_text,
            transform=ax.transAxes,
            horizontalalignment='right',
            verticalalignment='top',
            bbox=dict(facecolor='white', alpha=0.8)
        )
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        return fig