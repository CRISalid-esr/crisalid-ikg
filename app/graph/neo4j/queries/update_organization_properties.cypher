MATCH (o:Organisation {uid: $organization_uid})
SET o.type = $organization_type
RETURN o;