import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Paper, 
  Box, 
  FormControlLabel, 
  Switch,
  CircularProgress,
  Alert
} from '@mui/material';
import axios from 'axios';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [location, setLocation] = useState('');
  const [dynamicScraping, setDynamicScraping] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:7860/analyze', {
        url,
        company_name: companyName,
        location,
        dynamic_main: dynamicScraping
      }, {
        timeout: 600000 // 10 minutes timeout
      });

      // Store the analysis in localStorage
      const timestamp = new Date().toISOString();
      const analysisId = `analysis_${timestamp}`;
      localStorage.setItem(analysisId, JSON.stringify({
        id: analysisId,
        timestamp,
        companyName,
        data: response.data
      }));

      // Navigate to results page
      navigate(`/results/${analysisId}`);
    } catch (err) {
      console.error('Analysis request failed:', err);
      setError('Analysis request failed. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Company Analysis Tool
        </Typography>
        <Typography variant="body1" color="textSecondary" paragraph>
          Enter a company URL, name, and location to analyze its online presence and generate insights.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            margin="normal"
            required
            fullWidth
            id="url"
            label="Company Website URL"
            name="url"
            autoFocus
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
            placeholder="https://example.com"
          />
          <TextField
            margin="normal"
            required
            fullWidth
            id="companyName"
            label="Company Name"
            name="companyName"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            disabled={loading}
            placeholder="Example Inc."
          />
          <TextField
            margin="normal"
            fullWidth
            id="location"
            label="Company Location (Optional)"
            name="location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            disabled={loading}
            placeholder="City, Country"
          />
          <FormControlLabel
            control={
              <Switch
                checked={dynamicScraping}
                onChange={(e) => setDynamicScraping(e.target.checked)}
                name="dynamicScraping"
                color="primary"
                disabled={loading}
              />
            }
            label="Use dynamic scraping (slower but more thorough)"
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading || !url || !companyName}
          >
            {loading ? (
              <>
                <CircularProgress size={24} color="inherit" sx={{ mr: 1 }} />
                Analyzing (this may take 1-2 minutes)...
              </>
            ) : (
              'Analyze Company'
            )}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default HomePage;