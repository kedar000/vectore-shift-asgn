import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
    Typography,
    Card,
    CardContent,
    Divider
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'Hubspot': 'hubspot'
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            let response;

            if (integrationType === 'Hubspot') {
                response = await axios.post(
                    `http://localhost:8000/integrations/${endpoint}/get_hubspot_items`,
                    { access_token: credentials.access_token },
                    { headers: { 'Content-Type': 'application/json' } }
                );
            } else {
                const formData = new FormData();
                formData.append('credentials', JSON.stringify(credentials));
                response = await axios.post(
                    `http://localhost:8000/integrations/${endpoint}/load`,
                    formData
                );
            }

            setLoadedData(response.data);
        } catch (e) {
            alert(e?.response?.data?.detail || 'Error occurred');
        }
    };

    return (
        <Box display="flex" flexDirection="column" alignItems="center" width="100%">
            <Button
                onClick={handleLoad}
                sx={{ mt: 2 }}
                variant="contained"
            >
                Load Data
            </Button>
            <Button
                onClick={() => setLoadedData(null)}
                sx={{ mt: 1 }}
                variant="outlined"
            >
                Clear Data
            </Button>

            <Box width="100%" mt={4}>
                {Array.isArray(loadedData) && loadedData.length > 0 ? (
                    loadedData.map((item) => (
                        <Card key={item.id} sx={{ mb: 2, p: 2 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    {item.name}
                                </Typography>
                                <Divider sx={{ mb: 1 }} />
                                <Typography variant="body2"><strong>ID:</strong> {item.id}</Typography>
                                <Typography variant="body2"><strong>Email:</strong> {item.email}</Typography>
                                <Typography variant="body2"><strong>First Name:</strong> {item.raw_data.properties.firstname}</Typography>
                                <Typography variant="body2"><strong>Last Name:</strong> {item.raw_data.properties.lastname}</Typography>
                                <Typography variant="body2"><strong>Created At:</strong> {item.raw_data.createdAt}</Typography>
                                <Typography variant="body2"><strong>Updated At:</strong> {item.raw_data.updatedAt}</Typography>
                            </CardContent>
                        </Card>
                    ))
                ) : loadedData ? (
                    <TextField
                        label="Loaded Data"
                        value={JSON.stringify(loadedData, null, 2)}
                        multiline
                        rows={10}
                        fullWidth
                        InputLabelProps={{ shrink: true }}
                        disabled
                        sx={{ mt: 2 }}
                    />
                ) : null}
            </Box>
        </Box>
    );
};