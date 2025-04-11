import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Paper,
  Box,
  Tabs,
  Tab,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  Grid as MuiGrid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Card,
  CardContent,
  LinearProgress,
  Avatar,
  IconButton,
  Tooltip,
  Fade,
  useTheme
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import CodeIcon from '@mui/icons-material/Code';
import BusinessIcon from '@mui/icons-material/Business';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import GroupIcon from '@mui/icons-material/Group';
import HandshakeIcon from '@mui/icons-material/Handshake';
import ComputerIcon from '@mui/icons-material/Computer';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ShareIcon from '@mui/icons-material/Share';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

// Create a Grid component that accepts the item prop
const Grid = (props: any) => <MuiGrid {...props} />;

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analysis-tabpanel-${index}`}
      aria-labelledby={`analysis-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface StoredAnalysis {
  id: string;
  timestamp: string;
  companyName: string;
  data: any;
}

const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<StoredAnalysis | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [jsonDialogOpen, setJsonDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const theme = useTheme();

  useEffect(() => {
    if (id) {
      const storedAnalysis = localStorage.getItem(id);
      if (storedAnalysis) {
        setAnalysis(JSON.parse(storedAnalysis));
      }
      // Simulate loading for smoother transitions
      setTimeout(() => setLoading(false), 800);
    }
  }, [id]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleDownloadJson = () => {
    if (!analysis) return;
    
    const dataStr = JSON.stringify(analysis.data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${analysis.companyName.replace(/\s+/g, '_')}_analysis.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: `${analysis?.companyName} Analysis`,
        text: `Check out this analysis of ${analysis?.companyName}`,
        url: window.location.href,
      }).catch((error) => console.log('Error sharing', error));
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 10, textAlign: 'center' }}>
        <Typography variant="h4" gutterBottom>Loading Analysis</Typography>
        <LinearProgress sx={{ mt: 4, mb: 4 }} />
        <Typography variant="body1" color="textSecondary">
          Preparing your data visualization...
        </Typography>
      </Container>
    );
  }

  if (!analysis) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <Avatar sx={{ width: 60, height: 60, bgcolor: 'error.main', mx: 'auto', mb: 2 }}>
            <AssessmentIcon fontSize="large" />
          </Avatar>
          <Alert severity="error" sx={{ mb: 3 }}>
            Analysis not found. Please return to the home page and try again.
          </Alert>
          <Button 
            variant="contained" 
            onClick={() => navigate('/')}
            sx={{ mt: 2 }}
            size="large"
          >
            Return to Home
          </Button>
        </Paper>
      </Container>
    );
  }

  const insights = analysis.data.llm_generated_insights;
  
  // Prepare data for charts
  const swotData = [
    { name: 'Strengths', value: insights.swot_analysis.strengths.length, color: '#4caf50' },
    { name: 'Weaknesses', value: insights.swot_analysis.weaknesses.length, color: '#f44336' },
    { name: 'Opportunities', value: insights.swot_analysis.opportunities.length, color: '#2196f3' },
    { name: 'Threats', value: insights.swot_analysis.threats.length, color: '#ff9800' }
  ];
  
  const tabIcons = [
    <BusinessIcon />,
    <TrendingUpIcon />,
    <GroupIcon />,
    <HandshakeIcon />,
    <ComputerIcon />,
    <AssessmentIcon />
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          borderRadius: 2,
          background: `linear-gradient(to right, ${theme.palette.background.paper}, ${theme.palette.background.default})`,
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 2,
          flexDirection: { xs: 'column', sm: 'row' },
          gap: { xs: 2, sm: 0 }
        }}>
          <Box>
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 'bold',
                background: 'linear-gradient(45deg, #1976d2, #9c27b0)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              {analysis.companyName} Analysis
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Analysis performed on: {new Date(analysis.timestamp).toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Share Analysis">
              <IconButton onClick={handleShare} color="primary">
                <ShareIcon />
              </IconButton>
            </Tooltip>
            <Button 
              variant="outlined" 
              startIcon={<CodeIcon />}
              onClick={() => setJsonDialogOpen(true)}
              sx={{ mr: 1 }}
            >
              View Raw JSON
            </Button>
            <Button 
              variant="contained" 
              startIcon={<DownloadIcon />}
              onClick={handleDownloadJson}
            >
              Download JSON
            </Button>
          </Box>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            aria-label="analysis tabs"
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
            sx={{
              '& .MuiTab-root': {
                minHeight: '72px',
                textTransform: 'none',
                fontWeight: 'medium',
              }
            }}
          >
            {['SWOT Analysis', 'Transformation Opportunities', 'Leadership & Culture', 
              'Business Development', 'Technical Profile', 'Data Quality'].map((label, index) => (
              <Tab 
                key={index} 
                label={label} 
                icon={tabIcons[index]} 
                iconPosition="start"
                sx={{ 
                  borderRadius: '8px 8px 0 0',
                  transition: 'all 0.2s',
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(25, 118, 210, 0.08)',
                  }
                }}
              />
            ))}
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium' }}>
              SWOT Analysis Overview
            </Typography>
            <Typography variant="body1" paragraph color="textSecondary">
              A comprehensive analysis of {analysis.companyName}'s strengths, weaknesses, opportunities, and threats.
            </Typography>
            
            <Box sx={{ height: 250, mb: 4 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={swotData}
                    cx="50%"
                    cy="50%"
                    labelLine={true}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {swotData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Box>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card elevation={2} sx={{ height: '100%', bgcolor: 'rgba(76, 175, 80, 0.08)', borderLeft: '4px solid #4caf50' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: '#2e7d32', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: '#4caf50', color: 'white', p: 0.5, borderRadius: '50%', width: 24, height: 24, justifyContent: 'center', alignItems: 'center' }}>S</Box>
                    Strengths
                  </Typography>
                  <List>
                    {insights.swot_analysis.strengths.map((strength: string, index: number) => (
                      <ListItem key={`strength-${index}`} sx={{ py: 0.5 }}>
                        <ListItemText 
                          primary={strength} 
                          primaryTypographyProps={{ 
                            variant: 'body1',
                            sx: { 
                              fontWeight: index === 0 ? 'medium' : 'regular',
                              transition: 'all 0.2s',
                              '&:hover': { pl: 1 }
                            } 
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={2} sx={{ height: '100%', bgcolor: 'rgba(244, 67, 54, 0.08)', borderLeft: '4px solid #f44336' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: '#c62828', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: '#f44336', color: 'white', p: 0.5, borderRadius: '50%', width: 24, height: 24, justifyContent: 'center', alignItems: 'center' }}>W</Box>
                    Weaknesses
                  </Typography>
                  <List>
                    {insights.swot_analysis.weaknesses.map((weakness: string, index: number) => (
                      <ListItem key={`weakness-${index}`} sx={{ py: 0.5 }}>
                        <ListItemText 
                          primary={weakness} 
                          primaryTypographyProps={{ 
                            variant: 'body1',
                            sx: { 
                              fontWeight: index === 0 ? 'medium' : 'regular',
                              transition: 'all 0.2s',
                              '&:hover': { pl: 1 }
                            } 
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={2} sx={{ height: '100%', bgcolor: 'rgba(33, 150, 243, 0.08)', borderLeft: '4px solid #2196f3' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: '#0d47a1', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: '#2196f3', color: 'white', p: 0.5, borderRadius: '50%', width: 24, height: 24, justifyContent: 'center', alignItems: 'center' }}>O</Box>
                    Opportunities
                  </Typography>
                  <List>
                    {insights.swot_analysis.opportunities.map((opportunity: string, index: number) => (
                      <ListItem key={`opportunity-${index}`} sx={{ py: 0.5 }}>
                        <ListItemText 
                          primary={opportunity} 
                          primaryTypographyProps={{ 
                            variant: 'body1',
                            sx: { 
                              fontWeight: index === 0 ? 'medium' : 'regular',
                              transition: 'all 0.2s',
                              '&:hover': { pl: 1 }
                            } 
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={2} sx={{ height: '100%', bgcolor: 'rgba(255, 152, 0, 0.08)', borderLeft: '4px solid #ff9800' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: '#e65100', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: '#ff9800', color: 'white', p: 0.5, borderRadius: '50%', width: 24, height: 24, justifyContent: 'center', alignItems: 'center' }}>T</Box>
                    Threats
                  </Typography>
                  <List>
                    {insights.swot_analysis.threats.map((threat: string, index: number) => (
                      <ListItem key={`threat-${index}`} sx={{ py: 0.5 }}>
                        <ListItemText 
                          primary={threat} 
                          primaryTypographyProps={{ 
                            variant: 'body1',
                            sx: { 
                              fontWeight: index === 0 ? 'medium' : 'regular',
                              transition: 'all 0.2s',
                              '&:hover': { pl: 1 }
                            } 
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        {/* Continue with other TabPanels with similar enhancements */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium' }}>
              Transformation Opportunities
            </Typography>
            <Typography variant="body1" paragraph color="textSecondary">
              Key areas where {analysis.companyName} could transform their business for growth and innovation.
            </Typography>
          </Box>
          
          <Grid container spacing={3}>
            {insights.potential_transformation_angles.map((angle: string, index: number) => (
              <Grid item xs={12} md={6} key={`angle-${index}`}>
                <Card 
                  elevation={2} 
                  sx={{ 
                    p: 2, 
                    height: '100%', 
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 8px 16px rgba(0,0,0,0.1)'
                    },
                    borderLeft: '4px solid #9c27b0'
                  }}
                >
                  <CardContent>
                    <Typography 
                      variant="body1" 
                      sx={{ 
                        fontWeight: index < 2 ? 'medium' : 'regular',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: 1
                      }}
                    >
                      <Box 
                        component="span" 
                        sx={{ 
                          display: 'inline-flex', 
                          bgcolor: '#9c27b0', 
                          color: 'white', 
                          p: 0.5, 
                          borderRadius: '50%', 
                          width: 24, 
                          height: 24, 
                          justifyContent: 'center', 
                          alignItems: 'center',
                          flexShrink: 0,
                          mt: 0.5
                        }}
                      >
                        {index + 1}
                      </Box>
                      {angle}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium' }}>
              Leadership & Culture
            </Typography>
            <Typography variant="body1" paragraph color="textSecondary">
              Insights about {analysis.companyName}'s leadership team and company culture.
            </Typography>
          </Box>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card elevation={3} sx={{ height: '100%', borderRadius: 2, overflow: 'hidden' }}>
                <Box sx={{ bgcolor: '#5c6bc0', p: 2, color: 'white' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: 'rgba(255,255,255,0.2)', p: 0.5, borderRadius: '50%' }}>
                      👥
                    </Box>
                    Key Executives
                  </Typography>
                </Box>
                <CardContent>
                  {insights.key_executives_found && insights.key_executives_found.length > 0 ? (
                    <List sx={{ p: 0 }}>
                      {insights.key_executives_found.map((exec: any, index: number) => (
                        <ListItem 
                          key={`exec-${index}`}
                          sx={{ 
                            borderBottom: index < insights.key_executives_found.length - 1 ? '1px solid rgba(0,0,0,0.08)' : 'none',
                            transition: 'all 0.2s',
                            '&:hover': { bgcolor: 'rgba(0,0,0,0.03)' }
                          }}
                        >
                          <Avatar 
                            sx={{ 
                              mr: 2, 
                              bgcolor: `hsl(${index * 40}, 70%, 50%)`,
                              width: 40,
                              height: 40,
                              fontSize: '1rem'
                            }}
                          >
                            {exec.name.split(' ').map((n: string) => n[0]).join('')}
                          </Avatar>
                          <ListItemText 
                            primary={<Typography variant="body1" fontWeight="medium">{exec.name}</Typography>} 
                            secondary={exec.title} 
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Box sx={{ p: 2, textAlign: 'center' }}>
                      <Typography color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        No executive information found.
                      </Typography>
                      <Box 
                        component="img" 
                        src="https://cdn-icons-png.flaticon.com/512/3588/3588614.png" 
                        alt="No data"
                        sx={{ width: 80, height: 80, opacity: 0.5, mt: 2 }}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={3} sx={{ height: '100%', borderRadius: 2, overflow: 'hidden' }}>
                <Box sx={{ bgcolor: '#26a69a', p: 2, color: 'white' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: 'rgba(255,255,255,0.2)', p: 0.5, borderRadius: '50%' }}>
                      🚀
                    </Box>
                    Career Page Themes
                  </Typography>
                </Box>
                <CardContent>
                  {insights.career_page_themes && insights.career_page_themes.length > 0 ? (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                      {insights.career_page_themes.map((theme: string, index: number) => (
                        <Chip 
                          key={`theme-${index}`}
                          label={theme}
                          sx={{ 
                            bgcolor: `hsl(${index * 30}, 85%, 95%)`, 
                            color: `hsl(${index * 30}, 85%, 30%)`,
                            fontWeight: 'medium',
                            '&:hover': { transform: 'scale(1.05)' },
                            transition: 'transform 0.2s'
                          }}
                        />
                      ))}
                    </Box>
                  ) : (
                    <Box sx={{ p: 2, textAlign: 'center' }}>
                      <Typography color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        No career page themes found.
                      </Typography>
                      <Box 
                        component="img" 
                        src="https://cdn-icons-png.flaticon.com/512/4076/4076478.png" 
                        alt="No data"
                        sx={{ width: 80, height: 80, opacity: 0.5, mt: 2 }}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium' }}>
              Business Development
            </Typography>
            <Typography variant="body1" paragraph color="textSecondary">
              Key business development insights and potential opportunities for {analysis.companyName}.
            </Typography>
          </Box>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card elevation={3} sx={{ height: '100%', borderRadius: 2, overflow: 'hidden' }}>
                <Box sx={{ bgcolor: '#7e57c2', p: 2, color: 'white' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: 'rgba(255,255,255,0.2)', p: 0.5, borderRadius: '50%' }}>
                      📞
                    </Box>
                    Potential Contact Points
                  </Typography>
                </Box>
                <CardContent>
                  {insights.potential_contact_points && insights.potential_contact_points.length > 0 ? (
                    <List sx={{ p: 0 }}>
                      {insights.potential_contact_points.map((contact: string, index: number) => (
                        <ListItem 
                          key={`contact-${index}`}
                          sx={{ 
                            borderLeft: `4px solid hsl(${index * 40}, 70%, 60%)`,
                            pl: 2,
                            mb: 1,
                            borderRadius: '4px',
                            bgcolor: 'rgba(0,0,0,0.02)',
                            transition: 'all 0.2s',
                            '&:hover': { 
                              bgcolor: 'rgba(0,0,0,0.05)',
                              transform: 'translateX(4px)'
                            }
                          }}
                        >
                          <ListItemText 
                            primary={contact} 
                            primaryTypographyProps={{ 
                              variant: 'body1',
                              sx: { fontWeight: index === 0 ? 'medium' : 'regular' }
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Box sx={{ p: 2, textAlign: 'center' }}>
                      <Typography color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        No potential contact points identified.
                      </Typography>
                      <Box 
                        component="img" 
                        src="https://cdn-icons-png.flaticon.com/512/1055/1055645.png" 
                        alt="No data"
                        sx={{ width: 80, height: 80, opacity: 0.5, mt: 2 }}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={3} sx={{ height: '100%', borderRadius: 2, overflow: 'hidden' }}>
                <Box sx={{ bgcolor: '#ec407a', p: 2, color: 'white' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: 'rgba(255,255,255,0.2)', p: 0.5, borderRadius: '50%' }}>
                      💰
                    </Box>
                    M&A/Funding Mentions
                  </Typography>
                </Box>
                <CardContent>
                  {insights.explicit_mna_funding_mentions && insights.explicit_mna_funding_mentions.length > 0 ? (
                    <List sx={{ p: 0 }}>
                      {insights.explicit_mna_funding_mentions.map((mention: string, index: number) => (
                        <ListItem 
                          key={`mention-${index}`}
                          sx={{ 
                            bgcolor: 'rgba(236, 64, 122, 0.05)',
                            mb: 1,
                            borderRadius: '4px',
                            transition: 'all 0.2s',
                            '&:hover': { bgcolor: 'rgba(236, 64, 122, 0.1)' }
                          }}
                        >
                          <ListItemText 
                            primary={mention} 
                            primaryTypographyProps={{ 
                              variant: 'body1',
                              sx: { fontWeight: index === 0 ? 'medium' : 'regular' }
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Box sx={{ p: 2, textAlign: 'center' }}>
                      <Typography color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        No M&A or funding mentions found.
                      </Typography>
                      <Box 
                        component="img" 
                        src="https://cdn-icons-png.flaticon.com/512/2830/2830312.png" 
                        alt="No data"
                        sx={{ width: 80, height: 80, opacity: 0.5, mt: 2 }}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={4}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium' }}>
              Technical Profile
            </Typography>
            <Typography variant="body1" paragraph color="textSecondary">
              Technical insights and technology stack information for {analysis.companyName}.
            </Typography>
          </Box>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card elevation={3} sx={{ height: '100%', borderRadius: 2, overflow: 'hidden' }}>
                <Box sx={{ bgcolor: '#546e7a', p: 2, color: 'white' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: 'rgba(255,255,255,0.2)', p: 0.5, borderRadius: '50%' }}>
                      🔧
                    </Box>
                    Technology Flags
                  </Typography>
                </Box>
                <CardContent>
                  {insights.technology_flags && insights.technology_flags.length > 0 ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {insights.technology_flags.map((flag: string, index: number) => (
                        <Paper 
                          key={`flag-${index}`}
                          elevation={1}
                          sx={{ 
                            p: 2, 
                            borderLeft: '4px solid #546e7a',
                            transition: 'all 0.2s',
                            '&:hover': { 
                              transform: 'translateX(4px)',
                              boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
                            }
                          }}
                        >
                          <Typography variant="body1">{flag}</Typography>
                        </Paper>
                      ))}
                    </Box>
                  ) : (
                    <Box sx={{ p: 2, textAlign: 'center' }}>
                      <Typography color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        No technology flags identified.
                      </Typography>
                      <Box 
                        component="img" 
                        src="https://cdn-icons-png.flaticon.com/512/2910/2910896.png" 
                        alt="No data"
                        sx={{ width: 80, height: 80, opacity: 0.5, mt: 2 }}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card elevation={3} sx={{ height: '100%', borderRadius: 2, overflow: 'hidden' }}>
                <Box sx={{ bgcolor: '#fb8c00', p: 2, color: 'white' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: 'rgba(255,255,255,0.2)', p: 0.5, borderRadius: '50%' }}>
                      ⭐
                    </Box>
                    Review Site Presence
                  </Typography>
                </Box>
                <CardContent>
                  {insights.review_site_presence ? (
                    <Box sx={{ p: 2, bgcolor: 'rgba(251, 140, 0, 0.05)', borderRadius: 2 }}>
                      <Typography variant="body1" sx={{ lineHeight: 1.7 }}>
                        {insights.review_site_presence}
                      </Typography>
                    </Box>
                  ) : (
                    <Box sx={{ p: 2, textAlign: 'center' }}>
                      <Typography color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        No review site presence information available.
                      </Typography>
                      <Box 
                        component="img" 
                        src="https://cdn-icons-png.flaticon.com/512/1484/1484560.png" 
                        alt="No data"
                        sx={{ width: 80, height: 80, opacity: 0.5, mt: 2 }}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={5}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium' }}>
              Data Quality Assessment
            </Typography>
            <Typography variant="body1" paragraph color="textSecondary">
              Information about the quality and completeness of the data used in this analysis.
            </Typography>
          </Box>
          
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', mb: 3 }}>
                <Box sx={{ bgcolor: '#78909c', p: 2, color: 'white' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: 'rgba(255,255,255,0.2)', p: 0.5, borderRadius: '50%' }}>
                      📊
                    </Box>
                    Data Completeness Notes
                  </Typography>
                </Box>
                <CardContent>
                  {insights.data_completeness_notes && insights.data_completeness_notes.length > 0 ? (
                    <List>
                      {insights.data_completeness_notes.map((note: string, index: number) => (
                        <ListItem 
                          key={`note-${index}`}
                          sx={{ 
                            bgcolor: index % 2 === 0 ? 'rgba(0,0,0,0.02)' : 'transparent',
                            borderRadius: 1,
                            mb: 1
                          }}
                        >
                          <ListItemText 
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                                <Box 
                                  sx={{ 
                                    bgcolor: '#78909c', 
                                    color: 'white', 
                                    width: 24, 
                                    height: 24, 
                                    borderRadius: '50%', 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    justifyContent: 'center',
                                    flexShrink: 0,
                                    mt: 0.5
                                  }}
                                >
                                  {index + 1}
                                </Box>
                                <Typography variant="body1">{note}</Typography>
                              </Box>
                            } 
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Box sx={{ p: 2, textAlign: 'center' }}>
                      <Typography color="textSecondary" sx={{ fontStyle: 'italic' }}>
                        No data completeness notes available.
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12}>
              <Card 
                elevation={3} 
                sx={{ 
                  borderRadius: 2, 
                  overflow: 'hidden', 
                  borderLeft: '4px solid #ffc107'
                }}
              >
                <Box sx={{ bgcolor: '#ffc107', p: 2, color: 'white' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ display: 'inline-flex', bgcolor: 'rgba(255,255,255,0.2)', p: 0.5, borderRadius: '50%' }}>
                      ⚠️
                    </Box>
                    Analysis Caveat
                  </Typography>
                </Box>
                <CardContent>
                  <Paper 
                    elevation={0} 
                    sx={{ 
                      p: 3, 
                      bgcolor: 'rgba(255, 193, 7, 0.05)', 
                      border: '1px dashed rgba(255, 193, 7, 0.5)',
                      borderRadius: 2
                    }}
                  >
                    <Typography variant="body1" sx={{ fontStyle: 'italic', lineHeight: 1.7 }}>
                      {insights.speculation_caveat || "No analysis caveat provided."}
                    </Typography>
                  </Paper>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
      
      <Dialog
        open={jsonDialogOpen}
        onClose={() => setJsonDialogOpen(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            overflow: 'hidden'
          }
        }}
      >
        <DialogTitle sx={{ 
          bgcolor: '#1976d2', 
          color: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CodeIcon />
            Raw JSON Data
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          <Box 
            component="pre" 
            sx={{ 
              overflow: 'auto', 
              bgcolor: '#272822', 
              color: '#f8f8f2',
              p: 3, 
              m: 0,
              maxHeight: '70vh',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              lineHeight: 1.5
            }}
          >
            {JSON.stringify(analysis.data, null, 2)}
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2, bgcolor: '#f5f5f5' }}>
          <Button 
            onClick={() => setJsonDialogOpen(false)}
            variant="outlined"
          >
            Close
          </Button>
          <Button 
            onClick={handleDownloadJson} 
            startIcon={<DownloadIcon />}
            variant="contained"
          >
            Download
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ResultsPage;